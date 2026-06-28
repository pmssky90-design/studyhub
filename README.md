# StudyHub

StudyHub is a Python-based static site generator for a nationwide tutoring directory.

This stage intentionally does not generate, rewrite, summarize, or edit body content. The generator only builds the URL structure, hierarchy, SEO scaffolding, sitemap, robots file, breadcrumbs, schema, and internal links. Completed content can be connected later through Excel data.

## Run

```powershell
python generator.py
```

If Python is not on PATH in this Windows environment:

```powershell
& 'C:\Users\user\AppData\Local\Programs\Python\Python314\python.exe' generator.py
```

## URL Rules

Region pages keep the StudyNote-style keyword URL rule.

- `/전국과외/`
- `/서울과외/`
- `/서울과외/강남구과외/`
- `/서울과외/강남구과외/대치동과외/`
- `/대치동수학과외/`
- `/대치동영어과외/`
- `/대치동초등과외/`
- `/대치동중등과외/`
- `/대치동고등과외/`
- `/대치동초등수학과외/`
- `/대치동중등수학과외/`
- `/대치동고등수학과외/`
- `/대치동초등영어과외/`
- `/대치동중등영어과외/`
- `/대치동고등영어과외/`

## Implemented Structure

- 전국과외 -> 시도 -> 시군구 -> 읍면동
- 수학과외 -> 시도수학과외 -> 시군구수학과외 -> 읍면동수학과외
- 영어과외 -> 시도영어과외 -> 시군구영어과외 -> 읍면동영어과외
- 초등과외 -> 시도초등과외 -> 시군구초등과외 -> 읍면동초등과외
- 중등과외 -> 시도중등과외 -> 시군구중등과외 -> 읍면동중등과외
- 고등과외 -> 시도고등과외 -> 시군구고등과외 -> 읍면동고등과외

Math pages link to 초등수학과외, 중등수학과외, 고등수학과외.

English pages link to 초등영어과외, 중등영어과외, 고등영어과외.

## Modules

- `generator.py`: entrypoint
- `config.py`: domain, paths, category taxonomy
- `sitegen/regions.py`: CSV/XLSX region hierarchy loader
- `sitegen/urls.py`: StudyNote-style URL rules
- `sitegen/builder.py`: page graph, internal links, sitemap, robots
- `sitegen/render.py`: minimal structural HTML rendering
- `sitegen/seo.py`: canonical, Open Graph, JSON-LD schema
- `data/regions.csv`: sample region hierarchy
- `data/regions.xlsx`: optional full region hierarchy source

