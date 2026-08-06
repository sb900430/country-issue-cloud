# Country Issue Cloud Web

Static GitHub Pages client for the shared issue result Schema. The default data source reads `./data/v1`, while the deferred server deployment can switch to `ApiDataSource` without changing view logic.

## Local fixture preview

```powershell
.\scripts\build-pages-site.ps1 -Mode fixture -OutputDirectory .\preview-site
Set-Location .\preview-site
python -m http.server 8080
```

Open `http://localhost:8080`. The generated `preview-site/` directory is local-only and must not be committed.
