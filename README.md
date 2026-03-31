grpc-ui-client/
├── main.py                      # 入口
├── app/
│   ├── __init__.py
│   ├── app.py                   # 应用初始化
│
├── ui/
│   ├── __init__.py
│   ├── main_window.py           # 主窗口
│   ├── header_bar.py            # 顶部 toolbar
│   ├── left_panel.py            # 左侧（proto + API）
│   ├── center_panel.py          # 中间（请求）
│   ├── right_panel.py           # 右侧（结果）
│
├── handlers/
│   ├── __init__.py
│   ├── toolbar_handler.py       # toolbar事件
│   ├── api_handler.py           # API点击事件
│
├── services/
│   ├── __init__.py
│   ├── grpc_service.py          # gRPC调用（预留）
│   ├── proto_service.py         # proto解析（预留）
│
├── styles/
│   ├── style.css               # GTK样式
│
└── utils/
    ├── __init__.py
    ├── json_utils.py            # JSON格式化
