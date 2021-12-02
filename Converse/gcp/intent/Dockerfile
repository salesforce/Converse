FROM nvidia/cuda:10.1-runtime-ubuntu18.04
LABEL maintainer "NVIDIA CORPORATION <cudatools@nvidia.com>"

ENV CUDNN_VERSION 7.6.0.64
LABEL com.nvidia.cudnn.version="${CUDNN_VERSION}"


RUN apt-get update && apt-get install -y --no-install-recommends \
    locales \
    wget \
    build-essential \
    vim \
    htop \
    git less ssh cmake \
    zip unzip gzip bzip2 \
    gcc g++ \
    default-jdk \
    libcudnn7=$CUDNN_VERSION-1+cuda10.1 && \
    apt-mark hold libcudnn7 && \
    rm -rf /var/lib/apt/lists/*

RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

ENV PATH /opt/conda/bin:$PATH

RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-py37_4.9.2-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh && \
    /opt/conda/bin/conda clean -tipsy && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
    echo "conda activate base" >> ~/.bashrc

RUN conda install pytorch torchvision torchaudio cudatoolkit=10.1 -c pytorch
RUN conda install scikit-learn
RUN pip install pytorch-pretrained-BERT transformers spacy ftfy==4.4.3
RUN python -m spacy download en
RUN pip install scikit-learn grpcio duckling grpcio-tools
RUN pip install jpype1==0.7.5

RUN mkdir /workspace
WORKDIR /workspace
