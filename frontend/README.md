# Frontend module

The responsive HTML/CSS/JavaScript client is the current primary UI. GitHub Pages first serves it with generated static JSON through `StaticJsonDataSource`. A preserved `ApiDataSource` uses the same response schema for a later VPS/EC2 FastAPI deployment, so migration changes configuration and infrastructure rather than UI logic.
