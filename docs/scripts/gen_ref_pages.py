# SPDX-FileCopyrightText: 2026 PN5180-tagomatic contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Generate the code reference pages automatically."""

from pathlib import Path

import mkdocs_gen_files

# Module descriptions for better display names
module_descriptions = {
    "pn5180": "PN5180",
    "session": "Session",
    "iso14443a": "ISO 14443-A",
    "iso15693": "ISO 15693",
    "proxy": "Proxy",
    "constants": "Constants",
}

src = Path(__file__).parent.parent.parent / "src"
package_dir = src / "pn5180_tagomatic"

# First, create the API index page with generated links
api_index_content = """<!--
SPDX-FileCopyrightText: 2026 PN5180-tagomatic contributors
SPDX-License-Identifier: GPL-3.0-or-later
-->

# API Reference

This section provides detailed API documentation for all modules in PN5180-tagomatic.

The API documentation is automatically generated from the Python source code docstrings.

## Modules

"""

# Collect modules for the index
modules = []
for module_path in sorted(package_dir.glob("*.py")):
    module_name = module_path.stem
    
    # Skip __init__ and private modules
    if module_name.startswith("_"):
        continue
    
    modules.append(module_name)
    
    # Create the documentation path
    doc_path = Path("api", f"{module_name}.md")
    
    # Get the module title
    title = module_descriptions.get(module_name, module_name.replace("_", " ").title())
    
    # Add to index content
    api_index_content += f"- **[{title}]({module_name}.md)**: `pn5180_tagomatic.{module_name}`\n"
    
    # Generate the markdown content for each module
    with mkdocs_gen_files.open(doc_path, "w") as fd:
        # Write SPDX headers
        fd.write("<!--\n")
        fd.write("SPDX-FileCopyrightText: 2026 PN5180-tagomatic contributors\n")
        fd.write("SPDX-License-Identifier: GPL-3.0-or-later\n")
        fd.write("-->\n\n")
        
        # Write module title and mkdocstrings reference
        module_full_name = f"pn5180_tagomatic.{module_name}"
        fd.write(f"# {title} Module\n\n")
        fd.write(f"::: {module_full_name}\n")
    
    # Set the edit path for GitHub integration
    mkdocs_gen_files.set_edit_path(doc_path, module_path.relative_to(src.parent))

# Add usage pattern to index
api_index_content += """
## Quick Start

```python
from pn5180_tagomatic import PN5180

with PN5180("/dev/ttyACM0") as reader:
    with reader.start_session(0x00, 0x80) as session:
        card = session.connect_one_iso14443a()
        memory = card.read_memory()
```

## Module Organization

The package is organized into focused modules:

- **pn5180**: Main high-level interface
- **session**: RF communication session management  
- **iso14443a**: ISO 14443-A card implementation
- **iso15693**: ISO 15693 card implementation
- **proxy**: Low-level hardware communication
- **constants**: Enums, constants, and exceptions
"""

# Write the updated API index
with mkdocs_gen_files.open("api/index.md", "w") as fd:
    fd.write(api_index_content)
