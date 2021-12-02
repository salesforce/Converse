FROM nvidia/cuda:10.2-devel-ubuntu18.04
LABEL maintainer "NVIDIA CORPORATION <cudatools@nvidia.com>"

ENV CUDNN_VERSION 7.6.5.32
LABEL com.nvidia.cudnn.version="${CUDNN_VERSION}"

RUN apt-get update && apt-get install -y --no-install-recommends \
    locales \
    wget \
    build-essential \
    vim \
    htop \
    curl \
    git less ssh cmake \
    zip unzip gzip bzip2 \
    gcc g++ \
    default-jdk \
    libcudnn7=$CUDNN_VERSION-1+cuda10.2 \
    libcudnn7-dev=$CUDNN_VERSION-1+cuda10.2 \
    && apt-mark hold libcudnn7 && \
    rm -rf /var/lib/apt/lists/*

RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

ENV PATH /opt/conda/bin:$PATH

RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh && \
    /opt/conda/bin/conda clean -tipsy && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
    echo "conda activate base" >> ~/.bashrc

RUN wget http://pyyaml.org/download/libyaml/yaml-0.2.1.tar.gz && \
    tar -xzvf yaml-0.2.1.tar.gz && cd yaml-0.2.1 && \
    ./configure && \
    make && make install

RUN conda install pytorch torchvision cudatoolkit=10.2 -c pytorch
RUN conda install flask
RUN pip install cython
RUN pip install pyyaml \
    transformers \
    pytorch-pretrained-BERT
RUN pip install wrapt --upgrade --ignore-installed

RUN mkdir /workspace
WORKDIR /workspace

RUN git clone https://github.com/NVIDIA/apex
WORKDIR /workspace/apex
RUN pip install -v --no-cache-dir --global-option="--cpp_ext" --global-option="--cuda_ext" ./
WORKDIR /workspace