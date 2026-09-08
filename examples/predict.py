"""Offline inference from explicitly encoded features and a simulator-provided legal mask."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import onnxruntime as ort


def predict(model_path, metadata_path, inputs_path):
    model_path=Path(model_path)
    metadata=json.loads(Path(metadata_path).read_text(encoding='utf-8'))
    if hashlib.sha256(model_path.read_bytes()).hexdigest()!=metadata['onnxSha256']:
        raise ValueError('ONNX SHA256 mismatch')
    values=json.loads(Path(inputs_path).read_text(encoding='utf-8'))
    if values['contractId']!=metadata['contractId']:
        raise ValueError('Feature/action contract mismatch')
    x=np.asarray(values['features'],dtype=np.float32)
    raw_mask=np.asarray(values['legal_mask'])
    if raw_mask.dtype != np.bool_:
        raise ValueError('legal_mask must contain JSON true/false values')
    mask=raw_mask.astype(bool)
    if x.ndim!=2 or x.shape[1]!=metadata['featureEncoder']['dimension'] or not np.isfinite(x).all():
        raise ValueError('Invalid encoded features')
    if mask.shape!=(len(x),len(metadata['actionVocab']['actions'])) or not mask.any(axis=1).all():
        raise ValueError('Invalid or empty legal action mask; do not request an action')
    options=ort.SessionOptions()
    options.intra_op_num_threads=options.inter_op_num_threads=1
    session=ort.InferenceSession(str(model_path),options,providers=['CPUExecutionProvider'])
    logits,value,remaining=session.run(['policy_logits','value','remaining_steps'],{'features':x,'legal_mask':mask})
    if not all(np.isfinite(v).all() for v in (logits,value,remaining)):
        raise ValueError('Non-finite model outputs')
    selected=np.argmax(np.where(mask,logits,-np.inf),axis=1)
    return [dict(action=metadata['actionVocab']['actions'][int(index)],
                 predictedRemainingCalls=float(remaining[row]),uncalibratedValue=float(value[row]))
            for row,index in enumerate(selected)]


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model',default='artifacts/ruri-craft-g1.onnx')
    parser.add_argument('--metadata',default='metadata.json')
    parser.add_argument('--input',default='examples/example-input.json')
    args=parser.parse_args()
    print(json.dumps(predict(args.model,args.metadata,args.input),ensure_ascii=False,indent=2))
