"""Official static TopKV2 OM on the caller's preallocated buffers and stream."""
import ctypes as C
import os


class GeTopK:
    def __init__(self, path, scores, values, indices):
        import torch
        self.api = C.CDLL(os.environ["ASCEND_HOME_PATH"] + "/lib64/libascendcl.so", mode=C.RTLD_GLOBAL)
        ptr, size, uint = C.c_void_p, C.c_size_t, C.c_uint32

        def bind(name, args, ret=C.c_int):
            fn = getattr(self.api, name)
            fn.argtypes, fn.restype = args, ret
            return fn

        load = bind("aclmdlLoadFromFile", [C.c_char_p, C.POINTER(uint)])
        desc_new = bind("aclmdlCreateDesc", [], ptr)
        desc_get = bind("aclmdlGetDesc", [ptr, uint])
        num_in = bind("aclmdlGetNumInputs", [ptr], size)
        num_out = bind("aclmdlGetNumOutputs", [ptr], size)
        in_type = bind("aclmdlGetInputDataType", [ptr, size])
        out_type = bind("aclmdlGetOutputDataType", [ptr, size])
        in_size = bind("aclmdlGetInputSizeByIndex", [ptr, size], size)
        out_size = bind("aclmdlGetOutputSizeByIndex", [ptr, size], size)
        dataset_new = bind("aclmdlCreateDataset", [], ptr)
        buffer_new = bind("aclCreateDataBuffer", [ptr, size], ptr)
        dataset_add = bind("aclmdlAddDatasetBuffer", [ptr, ptr])
        self.execute = bind("aclmdlExecuteAsync", [uint, ptr, ptr, ptr])
        self.unload = bind("aclmdlUnload", [uint])
        self.destroy_buffer = bind("aclDestroyDataBuffer", [ptr])
        self.destroy_dataset = bind("aclmdlDestroyDataset", [ptr])
        self.destroy_desc = bind("aclmdlDestroyDesc", [ptr])
        self.model = uint()
        self.check(load(str(path).encode(), C.byref(self.model)))
        self.desc = desc_new()
        assert self.desc
        self.check(desc_get(self.desc, self.model))
        self.description = {"inputs": num_in(self.desc), "outputs": num_out(self.desc),
                            "input_dtype": in_type(self.desc, 0),
                            "output_dtypes": [out_type(self.desc, i) for i in range(2)],
                            "input_bytes": in_size(self.desc, 0),
                            "output_bytes": [out_size(self.desc, i) for i in range(2)]}
        assert self.description == {"inputs": 1, "outputs": 2, "input_dtype": 0,
                                    "output_dtypes": [0, 3], "input_bytes": 16384 * 4,
                                    "output_bytes": [2048 * 4, 2048 * 4]}
        self.tensors = (scores, values, indices)
        self.buffers = []

        def dataset(tensors):
            ds = dataset_new()
            assert ds
            for tensor in tensors:
                assert tensor.is_contiguous() and tensor.device.type == "npu"
                buf = buffer_new(ptr(tensor.data_ptr()), tensor.numel() * tensor.element_size())
                assert buf
                self.buffers.append(buf)
                self.check(dataset_add(ds, buf))
            return ds

        self.inputs, self.outputs = dataset([scores]), dataset([values, indices])
        self.stream = ptr(torch.npu.current_stream().npu_stream)

    @staticmethod
    def check(status):
        if status:
            raise RuntimeError(f"ACL error {status}")

    def run(self):
        self.check(self.execute(self.model, self.inputs, self.outputs, self.stream))

    def close(self):
        self.check(self.unload(self.model))
        for buffer in self.buffers:
            self.check(self.destroy_buffer(buffer))
        for dataset in [self.inputs, self.outputs]:
            self.check(self.destroy_dataset(dataset))
        self.check(self.destroy_desc(self.desc))
