FROM gsk_poc_base:0.0.1


# 更新 pip 并配置镜像源
RUN pip config set global.extra-index-url "https://mirrors.cernet.edu.cn/pypi/web/simple"
RUN pip install --upgrade pip setuptools wheel

# 设置工作目录
WORKDIR /app

# 拷贝依赖文件并安装
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝代码
COPY . /app

# 修改文件权限
RUN chmod -R 755 /app

# RUN mkdir -p /usr/local/nltk_data
# COPY /home/zzhan1/nltk_data /usr/local/nltk_data