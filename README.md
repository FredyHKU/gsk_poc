gsk_poc


接口1：
POST /create_session
```sh

curl -X POST http://127.0.0.1:8000/create_session

# 返回值
{"session_id":"eef227733e5a4d40","status":"success","message":"Session created successfully"}

```

接口2：
POST /explore_docs/{session_id}
```sh

curl -X POST http://127.0.0.1:8000/explore_docs/eef227733e5a4d40 \
-H "Content-Type: application/json" \
-d '{"user_message": "国药集团物流服务中押车服务的收费准则是什么"}'

# 返回值

{"documents":[{"document_id":"doc123","document_name":"国药集团物流合同.pdf","preview":"xxxxxxxxxxxxxx","create_time":1740319113725,"update_time":1740319113725}],"message":"Found 1 relevant document","status":"success"}

```

接口3：
POST /add_docs/{session_id}


```sh
curl -X POST http://127.0.0.1:8000/add_docs/eef227733e5a4d40 \
-H "Content-Type: application/json" \
-d '{"document_id": ["doc123", "doc456"]}'

# 返回值
{"status":"success","message":"Document 国药集团物流合同.pdf added to session"}
```


接口4：
POST /chat_on_docs/{session_id}
```sh
#会话有文档
curl -X POST http://127.0.0.1:8000/chat_on_docs/eef227733e5a4d40 \
-H "Content-Type: application/json" \
-d '{"message": "国药集团物流服务中押车服务的收费准则是什么"}' \
-N

# 返回值
event: message
data: {"role": "assistant", "content": "收费"}

event: message
data: {"role": "assistant", "content": "信息"}

event: message
data: {"role": "assistant", "content": "。"}

event: end
data: [DONE]


#会话无文档
curl -X POST http://127.0.0.1:8000/chat_on_docs/5fb484dd937c47db \
-H "Content-Type: application/json" \
-d '{"message": "国药集团物流服务中押车服务的收费准则是什么"}' 
# 返回值
{"detail":{"status":"error","err_code":1001,"message":"No document added to this session."}}
```




