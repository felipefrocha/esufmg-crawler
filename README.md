# Crawler UFMG

## Ementas dos cursos da UFMG

### Função 

O crawler abaixo busca todos os dados da UFMG de ementas de seus cursos disponibilizados na página principal

### Objetivo

Tornar mais simples a consulta dos dados de diversos cursos e disciplinas para elencar ementas durante a solicitação de eliminiação de créditos

### Requisitos
* Instale o docker
* Use o comando abaixo:
```bash
docker build -t felipefrocha89/esufmg:crawler . && docker run -it --rm -v $PWD:/app -w /app felipefrocha89/esufmg:crawler __init__.py
# OR 
make
```
 


## Side effects
* Estudo de paralelismo em Python
* Funcionamento de Crawler em Python
* Engenharia de soluções

## Contribuição
* Faça um fork do projeto
* Solicite um PR
* Utilize o template disponibilizado e descreva o que foi feito


