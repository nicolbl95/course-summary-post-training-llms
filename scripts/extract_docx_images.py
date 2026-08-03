from __future__ import annotations

import shutil
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = PROJECT_ROOT / "documents-source"

DOCUMENTS = {
    "1 Intro.docx": PROJECT_ROOT / "assets" / "01-introduction",
    "2 SFT.docx": PROJECT_ROOT / "assets" / "02-sft",
    "3. DPO.docx": PROJECT_ROOT / "assets" / "03-dpo",
    "4 RL.docx": PROJECT_ROOT / "assets" / "04-reinforcement-learning",
    "5 Conclusion.docx": PROJECT_ROOT / "assets" / "05-conclusion",
}

REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def get_image_targets_in_order(docx_path: Path) -> list[str]:
    """Retourne les images dans leur ordre d’apparition dans le document."""

    with zipfile.ZipFile(docx_path) as archive:
        document_xml = archive.read("word/document.xml")
        relationships_xml = archive.read("word/_rels/document.xml.rels")

    relationships_root = ET.fromstring(relationships_xml)
    relationships: dict[str, str] = {}

    for relationship in relationships_root.findall(
        f"{{{PACKAGE_REL_NS}}}Relationship"
    ):
        relationship_id = relationship.attrib.get("Id")
        target = relationship.attrib.get("Target")

        if relationship_id and target and "media/" in target:
            relationships[relationship_id] = target

    document_root = ET.fromstring(document_xml)
    image_targets: list[str] = []

    for element in document_root.iter():
        embed_id = element.attrib.get(f"{{{REL_NS}}}embed")

        if embed_id and embed_id in relationships:
            target = relationships[embed_id]

            if target not in image_targets:
                image_targets.append(target)

    return image_targets


def clear_output_directory(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    for item in output_dir.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)


def extract_images(docx_path: Path, output_dir: Path) -> int:
    clear_output_directory(output_dir)

    image_targets = get_image_targets_in_order(docx_path)

    with zipfile.ZipFile(docx_path) as archive:
        for index, target in enumerate(image_targets, start=1):
            archive_path = target

            if not archive_path.startswith("word/"):
                archive_path = f"word/{archive_path}"

            image_data = archive.read(archive_path)
            extension = Path(target).suffix.lower() or ".png"

            output_name = f"capture-{index:02d}{extension}"
            output_path = output_dir / output_name
            output_path.write_bytes(image_data)

            relative_path = output_path.relative_to(PROJECT_ROOT)
            print(f"  Créée : {relative_path}")

    return len(image_targets)


def main() -> int:
    if not SOURCE_DIR.exists():
        print(
            "Erreur : le dossier documents-source n’existe pas.",
            file=sys.stderr,
        )
        return 1

    total_images = 0

    for filename, output_dir in DOCUMENTS.items():
        docx_path = SOURCE_DIR / filename

        if not docx_path.exists():
            print(f"\nDocument introuvable : {filename}")
            continue

        print(f"\nExtraction de : {filename}")

        try:
            count = extract_images(docx_path, output_dir)
        except (zipfile.BadZipFile, KeyError, OSError) as error:
            print(f"  Erreur : {error}")
            continue

        total_images += count
        print(f"  {count} image(s) extraite(s).")

    print(f"\nTerminé : {total_images} image(s) extraites.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
