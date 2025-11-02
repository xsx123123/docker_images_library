# Author  : JZHANG
# Date    : 2025-11-1
# Version : 1.0.2v (Fixed Permissions)

# 1) 选择轻量基底镜像
# (默认用户是 'mambauser')
FROM mambaorg/micromamba:1.5.10

# 2) 切换到 ROOT 用户来安装系统依赖
# ----------------------------------------------------
USER root
# ----------------------------------------------------

# 3) 设置工作目录 & UPDATE (现在以 root 身份运行)
SHELL ["/bin/bash", "-lc"]
WORKDIR /opt
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        procps \
        bash \
        coreutils \
        gawk \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# 4) 切换回 mambauser 来创建环境
# (Micromamba 的 /opt/conda 目录归 mambauser 所有)
# ----------------------------------------------------
USER mambauser
# ----------------------------------------------------
# 5) 创建环境并安装 (现在以 mambauser 身份运行)
RUN micromamba create -y -n sambamba_env -c conda-forge -c bioconda sambamba=1.0.1 && \
    micromamba clean -a -y

# 6) 添加环境变量
# (ENV 指令不受 USER 切换的影响)
ENV PATH=/opt/conda/envs/sambamba_env/bin:$PATH

# 7) 设置默认命令 
CMD ["sambamba", "version"]