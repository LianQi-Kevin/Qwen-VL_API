# init network turbo
#source /etc/network_turbo

# init huggingface
export HF_HOME=/root/autodl-tmp/huggingface
export TRANSFORMERS_OFFLINE=1

# run OpenAI API server
cd /root/Qwen-VL_API || exit
source /root/venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 6006 --reload

#/root/venv/bin/python /root/Qwen-VL_API/main.py \
#  --server-port 6006 \
#  --server-name '0.0.0.0'