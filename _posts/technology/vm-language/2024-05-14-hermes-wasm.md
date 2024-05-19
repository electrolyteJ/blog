---
layout: post
title: React Native |  Hermes Support WASM
description:  WASM 字节码
tag:
- vm-language
- cross-platform
---

## VM
lib/VM/Interpreter.cpp
```cpp
#ifdef HERMES_RUN_WASM
      // Asm.js/Wasm Intrinsics
      CASE(Add32) {
        O1REG(Add32) = HermesValue::encodeUntrustedNumberValue(
            (int32_t)(int64_t)(O2REG(Add32).getNumber() +
                               O3REG(Add32).getNumber()));
        ip = NEXTINST(Add32);
        DISPATCH;
      }
      CASE(Sub32) {
        O1REG(Sub32) = HermesValue::encodeUntrustedNumberValue(
            (int32_t)(int64_t)(O2REG(Sub32).getNumber() -
                               O3REG(Sub32).getNumber()));
        ip = NEXTINST(Sub32);
        DISPATCH;
      }
      CASE(Mul32) {
        // Signedness matters for multiplication, but low 32 bits are the same
        // regardless of signedness.
        const uint32_t arg0 = (uint32_t)(int32_t)(O2REG(Mul32).getNumber());
        const uint32_t arg1 = (uint32_t)(int32_t)(O3REG(Mul32).getNumber());
        O1REG(Mul32) =
            HermesValue::encodeUntrustedNumberValue((int32_t)(arg0 * arg1));
        ip = NEXTINST(Mul32);
        DISPATCH;
      }
      CASE(Divi32) {
        const int32_t arg0 = (int32_t)(O2REG(Divi32).getNumber());
        const int32_t arg1 = (int32_t)(O3REG(Divi32).getNumber());
        O1REG(Divi32) = HermesValue::encodeUntrustedNumberValue(arg0 / arg1);
        ip = NEXTINST(Divi32);
        DISPATCH;
      }
      CASE(Divu32) {
        const uint32_t arg0 = (uint32_t)(int32_t)(O2REG(Divu32).getNumber());
        const uint32_t arg1 = (uint32_t)(int32_t)(O3REG(Divu32).getNumber());
        O1REG(Divu32) =
            HermesValue::encodeUntrustedNumberValue((int32_t)(arg0 / arg1));
        ip = NEXTINST(Divu32);
        DISPATCH;
      }

      CASE(Loadi8) {
        auto *mem = vmcast<JSTypedArrayBase>(O2REG(Loadi8));
        int8_t *basePtr = reinterpret_cast<int8_t *>(mem->begin(runtime));
        const uint32_t addr = (uint32_t)(int32_t)(O3REG(Loadi8).getNumber());
        O1REG(Loadi8) = HermesValue::encodeUntrustedNumberValue(basePtr[addr]);
        ip = NEXTINST(Loadi8);
        DISPATCH;
      }
      ...
```
wasm 字节码在Interpreter解释器中被执行


## Compiler

- lib/IR/IRBuilder.cpp：生成中间文件
- lib/IR/IRVerifier.cpp：中间文件验证
- lib/Optimizer/Wasm目录：wasm 优化器
- lib/Optimizer/PassManager/Pipeline.cpp：流水线
- lib/Optimizer/Scalar/InstSimplify.cpp：指令化
- lib/BCGen/HBC/ISel.cpp: 生成 wasm 字节码





lib/BCGen/HBC/ISel.cpp
```cpp
#ifdef HERMES_RUN_WASM
void HBCISel::generateCallIntrinsicInst(
    CallIntrinsicInst *Inst,
    BasicBlock *next) {
  // Store instrinsics use 3 input registers. Binary Arithmetic and Load
  // intrinsics use 2 input registers and 1 result register.
  auto arg1 = encodeValue(Inst->getArgument(0));
  auto arg2 = encodeValue(Inst->getArgument(1));
  unsigned res = -1;

  // Result register is not used in store instrinsics, but is still allocated.
  if (Inst->getIntrinsicsIndex() < WasmIntrinsics::__uasm_store8)
    res = encodeValue(Inst);

  switch (Inst->getIntrinsicsIndex()) {
    // Binary Arithmetic
    case WasmIntrinsics::__uasm_add32:
      BCFGen_->emitAdd32(res, arg1, arg2);
      break;
    case WasmIntrinsics::__uasm_sub32:
      BCFGen_->emitSub32(res, arg1, arg2);
      break;
    case WasmIntrinsics::__uasm_mul32:
      BCFGen_->emitMul32(res, arg1, arg2);
      break;
    case WasmIntrinsics::__uasm_divi32:
      BCFGen_->emitDivi32(res, arg1, arg2);
      break;
    case WasmIntrinsics::__uasm_divu32:
      BCFGen_->emitDivu32(res, arg1, arg2);
      break;

    // Load
    case WasmIntrinsics::__uasm_loadi8:
      BCFGen_->emitLoadi8(res, arg1, arg2);
      break;
    case WasmIntrinsics::__uasm_loadu8:
      BCFGen_->emitLoadu8(res, arg1, arg2);
      break;
    case WasmIntrinsics::__uasm_loadi16:
      BCFGen_->emitLoadi16(res, arg1, arg2);
      break;
    case WasmIntrinsics::__uasm_loadu16:
      BCFGen_->emitLoadu16(res, arg1, arg2);
      break;
    case WasmIntrinsics::__uasm_loadi32:
      BCFGen_->emitLoadi32(res, arg1, arg2);
      break;
    case WasmIntrinsics::__uasm_loadu32:
      BCFGen_->emitLoadu32(res, arg1, arg2);
      break;

    // Store
    case WasmIntrinsics::__uasm_store8:
      BCFGen_->emitStore8(arg1, arg2, encodeValue(Inst->getArgument(2)));
      break;
    case WasmIntrinsics::__uasm_store16:
      BCFGen_->emitStore16(arg1, arg2, encodeValue(Inst->getArgument(2)));
      break;
    case WasmIntrinsics::__uasm_store32:
      BCFGen_->emitStore32(arg1, arg2, encodeValue(Inst->getArgument(2)));
      break;

    default:
      break;
  }
}
#endif
```





# *参考资料*

[WebAssembly](https://developer.mozilla.org/en-US/docs/WebAssembly)

[WASI proposals](https://github.com/WebAssembly/WASI/blob/main/Proposals.md)
