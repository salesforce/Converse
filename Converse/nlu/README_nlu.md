## Run NLU (NER/Intent/Coreference) services in docker container


First of all, download the two files *models.tar* and *coref.tar.bz2* from the url https://console.cloud.google.com/storage/browser/sfr-nlu-data-research


### NER and Intent


1. Decompress the file models.tar

```
  $ tar xvf models.tar # untar to generate a model directory (note as MODELS_DIR)

```

2. Generate NER docker image 

```
  $ cd ner_converse
  $ docker build -t ner -f ../Dockerfile.nlu .
```

3. Run the NER service

```
  $ docker run --name myner -v {MODELS_DIR}:/workspace/models -p 50051:50051 ner
```

4. Verify the running of NER service

```
  $ python ./client.py
```

5. Generate Intent docker image 

```
  $ cd intent_converse
  $ docker build -t intent -f ../Dockerfile.nlu .
```

6. Run the Intent service

```
  $ docker run --name myintent -v {MODELS_DIR}:/workspace/models -p 9001:9001 intent
```

7. Verify the running of Intent service

```
  $ python ./client.py
```

### Coreference


1. Decompress the file coref.tar.bz2

```
  $ tar xvf coref.tar.bz2 # untar to generate a model directory (note as E2E-COREF-DIR)
```

2. Generate Coreference docker image 

```
  $ cd coref_converse
  $ docker build -t coref .
```

3. Run the Coreference GRPC service (The Coreference service is memory intensive. Please increase you docker memory quota to 10GB and swap memory to 2GB)

```
  $ docker run --name mycoref -v ${E2E-COREF-DIR}:/export/home/e2e-coref --memory="10g" --memory-swap="11g" -p 50052:50051 coref

```

4. Verify the running of the Coreference service

```
  $ python ./client.py
```

Finally with all NLU services up, please modify the service_channel in [model configuration file](../bot_configs/dial_info_config.yaml) as follows:

```

Models:
  ner:
    ...
    init_args:
      service_channel: 127.0.0.1:50051
    ...
  intent:
    ...
    init_args:
      service_channel: 127.0.0.1:9001
    ...
  coref:
    ...
    init_args:
      service_channel: 127.0.0.1:50052
    ...

```
