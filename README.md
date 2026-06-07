# 家庭出游相册

这是一个运行在 Ubuntu 家庭服务器上的照片和视频整理系统。

第一版目标：

- 手动把手机照片和视频复制到 `incoming/`
- 扫描媒体文件并提取元数据
- 自动归并成一次次出游记录
- 在家庭局域网通过网页查看

默认目录：

```text
family-album/
  incoming/
  library/originals/
  library/thumbnails/
  data/album.sqlite
  exports/journals/
```

本地开发：

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
pytest -v
```

## Docker 运行

```bash
docker compose up --build
```

浏览器访问：

```text
http://localhost:8000
```

在 Ubuntu 家庭服务器上，把 `./family-album` 换成外接硬盘或服务器上的真实目录即可。

## 第一版验收清单

- [ ] 可以启动 Web 服务
- [ ] 首页可以在局域网浏览器访问
- [ ] 可以把照片或视频放入 `incoming/`
- [ ] 扫描流程可以登记媒体文件并跳过重复文件
- [ ] 出游聚合算法可以把相近时间的媒体归为一组
- [ ] 可以通过服务函数重命名出游记录和标记精选媒体
