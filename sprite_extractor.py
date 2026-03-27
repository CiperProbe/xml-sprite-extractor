#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Tuple, Optional
from PIL import Image, ImageDraw


class SubTexture:
    """Represents a subtexture with its properties"""
    
    def __init__(self, name: str, x: int, y: int, width: int, height: int, 
                 frameX: int = 0, frameY: int = 0, frameWidth: int = None, 
                 frameHeight: int = None):
        self.name = name
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.frameX = frameX
        self.frameY = frameY
        self.frameWidth = frameWidth if frameWidth is not None else width
        self.frameHeight = frameHeight if frameHeight is not None else height
    
    def __repr__(self):
        return f"SubTexture(name='{self.name}', x={self.x}, y={self.y}, w={self.width}, h={self.height})"


class SpriteSheetExtractor:
    """Extracts subtextures from sprite sheets using Adobe Animate XML data"""
    
    def __init__(self, xml_path: str, sprite_sheet_path: str):
        self.xml_path = Path(xml_path)
        self.sprite_sheet_path = Path(sprite_sheet_path)
        self.subtextures: Dict[str, SubTexture] = {}
        self.sprite_sheet: Optional[Image.Image] = None
    
    def _sanitize_filename(self, name: str) -> str:
        return name.replace(" ", "_")
        
    def load_xml(self) -> None:
        if not self.xml_path.exists():
            raise FileNotFoundError(f"XML file not found: {self.xml_path}")
        
        try:
            tree = ET.parse(self.xml_path)
            root = tree.getroot()
            
            texture_atlas = root
            if root.tag != "TextureAtlas":
                texture_atlas = root.find(".//TextureAtlas")
                if texture_atlas is None:
                    raise ValueError("No TextureAtlas element found in XML")
            
            for subtexture_elem in texture_atlas.findall("SubTexture"):
                name = subtexture_elem.get("name")
                if name is None:
                    continue
                
                x = int(subtexture_elem.get("x", 0))
                y = int(subtexture_elem.get("y", 0))
                width = int(subtexture_elem.get("width", 0))
                height = int(subtexture_elem.get("height", 0))
                frameX = int(subtexture_elem.get("frameX", 0))
                frameY = int(subtexture_elem.get("frameY", 0))
                frameWidth = int(subtexture_elem.get("frameWidth", width))
                frameHeight = int(subtexture_elem.get("frameHeight", height))
                
                subtexture = SubTexture(
                    name=name, x=x, y=y, width=width, height=height,
                    frameX=frameX, frameY=frameY, 
                    frameWidth=frameWidth, frameHeight=frameHeight
                )
                
                self.subtextures[name] = subtexture
                
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML format: {e}")
    
    def load_sprite_sheet(self) -> None:
        if not self.sprite_sheet_path.exists():
            raise FileNotFoundError(f"Sprite sheet not found: {self.sprite_sheet_path}")
        
        try:
            self.sprite_sheet = Image.open(self.sprite_sheet_path)
            if self.sprite_sheet.mode != 'RGBA':
                self.sprite_sheet = self.sprite_sheet.convert('RGBA')
        except Exception as e:
            raise ValueError(f"Failed to load sprite sheet: {e}")
    
    def extract_subtexture(self, texture_name: str, offset_x: int = 0, offset_y: int = 0) -> Image.Image:
        if texture_name not in self.subtextures:
            raise ValueError(f"SubTexture '{texture_name}' not found in XML")
        
        if self.sprite_sheet is None:
            raise ValueError("Sprite sheet not loaded")
        
        subtexture = self.subtextures[texture_name]
        
        bbox = (subtexture.x, subtexture.y, 
                subtexture.x + subtexture.width, 
                subtexture.y + subtexture.height)
        
        extracted = self.sprite_sheet.crop(bbox)
        
        if subtexture.frameX != 0 or subtexture.frameY != 0:
            frame_canvas = Image.new('RGBA', 
                                    (subtexture.frameWidth, subtexture.frameHeight), 
                                    (0, 0, 0, 0))
            
            paste_x = -subtexture.frameX + offset_x
            paste_y = -subtexture.frameY + offset_y
            
            if (paste_x < subtexture.frameWidth and paste_y < subtexture.frameHeight and
                paste_x + extracted.width > 0 and paste_y + extracted.height > 0):
                
                src_x = max(0, -paste_x)
                src_y = max(0, -paste_y)
                dst_x = max(0, paste_x)
                dst_y = max(0, paste_y)
                
                crop_width = min(extracted.width - src_x, subtexture.frameWidth - dst_x)
                crop_height = min(extracted.height - src_y, subtexture.frameHeight - dst_y)
                
                if crop_width > 0 and crop_height > 0:
                    cropped_extracted = extracted.crop((src_x, src_y, src_x + crop_width, src_y + crop_height))
                    frame_canvas.paste(cropped_extracted, (dst_x, dst_y))
            
            extracted = frame_canvas
        elif offset_x != 0 or offset_y != 0:
            new_width = extracted.width + abs(offset_x)
            new_height = extracted.height + abs(offset_y)
            
            offset_canvas = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
            
            paste_x = max(0, offset_x)
            paste_y = max(0, offset_y)
            
            offset_canvas.paste(extracted, (paste_x, paste_y))
            extracted = offset_canvas
        
        return extracted
    
    def save_subtexture(self, texture_name: str, output_path: str, 
                       offset_x: int = 0, offset_y: int = 0) -> None:
        extracted = self.extract_subtexture(texture_name, offset_x, offset_y)
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            extracted.save(output_path, "PNG")
            print(f"Saved '{texture_name}' to {output_path}")
        except Exception as e:
            raise ValueError(f"Failed to save image: {e}")
    
    def list_subtextures(self) -> None:
        print(f"Found {len(self.subtextures)} subtextures:")
        for name, subtexture in sorted(self.subtextures.items()):
            print(f"  {name}: {subtexture.width}x{subtexture.height} at ({subtexture.x}, {subtexture.y})")
    
    def extract_all(self, output_dir: str, offset_x: int = 0, offset_y: int = 0) -> None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for texture_name in self.subtextures:
            sanitized_name = self._sanitize_filename(texture_name)
            output_path = output_dir / f"{sanitized_name}.png"
            try:
                self.save_subtexture(texture_name, output_path, offset_x, offset_y)
            except Exception as e:
                print(f"Error extracting '{texture_name}': {e}")


def main():
    script_dir = Path(__file__).parent
    default_import_dir = script_dir / "imported"
    default_extracted_dir = script_dir / "extracted"
    
    parser = argparse.ArgumentParser(
        description="Extract subtextures from Adobe Animate sprite sheets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s sprite.xml sprite.png -t "player_walk" -o output.png
  %(prog)s sprite.xml sprite.png -l
  %(prog)s sprite.xml sprite.png -a ./extracted/
  %(prog)s sprite.xml sprite.png -t "enemy" --offset 10 5 -o enemy_offset.png
  %(prog)s -l  # Auto-discover files in imported/ folder
  %(prog)s -a  # Extract all to extracted/ folder
        """
    )
    
    parser.add_argument("xml", nargs='?', help="Path to Adobe Animate XML file (optional if using -l or -a without arguments)")
    parser.add_argument("sprite", nargs='?', help="Path to sprite sheet image (optional if using -l or -a without arguments)")
    parser.add_argument("-t", "--texture", help="Name of subtexture to extract")
    parser.add_argument("-o", "--output", help="Output path for extracted texture")
    parser.add_argument("-l", "--list", action="store_true", help="List all available subtextures")
    parser.add_argument("-a", "--all", action="store_true", help="Extract all subtextures to directory")
    parser.add_argument("--offset", nargs=2, type=int, metavar=("X", "Y"), 
                       default=[0, 0], help="Offset to apply (X Y)")
    
    args = parser.parse_args()
    
    xml_file = args.xml
    sprite_file = args.sprite
    
    if not xml_file and not sprite_file:
        if not default_import_dir.exists():
            print(f"Import directory not found: {default_import_dir}")
            print("Please create 'imported' folder and place XML and PNG files there.")
            sys.exit(1)
        
        xml_files = list(default_import_dir.glob("*.xml"))
        if not xml_files:
            print(f"No XML files found in {default_import_dir}")
            sys.exit(1)
        
        xml_file = str(xml_files[0])
        print(f"Using XML file: {xml_file}")
        
        xml_name = Path(xml_file).stem
        png_candidates = [
            default_import_dir / f"{xml_name}.png",
            default_import_dir / f"{xml_name}.PNG"
        ]
        
        for png_candidate in png_candidates:
            if png_candidate.exists():
                sprite_file = str(png_candidate)
                print(f"Using sprite sheet: {sprite_file}")
                break
        
        if not sprite_file:
            print(f"No matching PNG file found for {xml_file}")
            print("Please place the corresponding sprite sheet in the imported folder.")
            sys.exit(1)
    
    if not args.list and not args.texture and not args.all:
        parser.error("Must specify --texture, --list, or --all")
    
    if args.texture and not args.output:
        sanitized_texture_name = args.texture.replace(" ", "_")
        args.output = str(default_extracted_dir / f"{sanitized_texture_name}.png")
    
    if args.all and not hasattr(args, 'all_dir'):
        args.all_dir = str(default_extracted_dir)
    
    try:
        extractor = SpriteSheetExtractor(xml_file, sprite_file)
        extractor.load_xml()
        extractor.load_sprite_sheet()
        
        if args.list:
            extractor.list_subtextures()
        
        if args.texture:
            extractor.save_subtexture(args.texture, args.output, 
                                   args.offset[0], args.offset[1])
        
        if args.all:
            extractor.extract_all(args.all_dir, args.offset[0], args.offset[1])
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
