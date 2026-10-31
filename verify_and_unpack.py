"""Verify the downloaded transport, reconstruct the sealed ZIP, and extract it safely."""
from pathlib import Path
import hashlib,json,sys,zipfile

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()

def main():
    root=Path(__file__).resolve().parent
    m=json.loads((root/'transport_manifest.json').read_text(encoding='utf-8'))
    name=m['archive_filename']
    if Path(name).name!=name:raise SystemExit('Invalid archive filename')
    output=root/name;partial=root/(name+'.partial');project=root/'MIRAGE-CAD'
    if project.exists():raise SystemExit('MIRAGE-CAD already exists; use a fresh extraction directory.')
    if not output.exists():
        if partial.exists():raise SystemExit('An earlier partial output exists; use a fresh directory.')
        h=hashlib.sha256();total=0
        with partial.open('xb') as out:
            for item in m['parts']:
                file=item['file']
                if Path(file).name!=file:raise SystemExit('Invalid part filename')
                p=root/file
                if digest(p)!=item['sha256']:raise SystemExit('Part checksum mismatch: '+file)
                with zipfile.ZipFile(p) as z:
                    if z.namelist()!=['payload.bin']:raise SystemExit('Invalid part member list')
                    chunk=z.read('payload.bin')
                if len(chunk)!=item['payload_bytes'] or hashlib.sha256(chunk).hexdigest()!=item['payload_sha256']:
                    raise SystemExit('Payload checksum mismatch: '+file)
                out.write(chunk);h.update(chunk);total+=len(chunk)
        if total!=m['archive_bytes'] or h.hexdigest()!=m['archive_sha256']:
            raise SystemExit('Whole-archive checksum mismatch; extraction refused.')
        partial.rename(output)
    if digest(output)!=m['archive_sha256']:raise SystemExit('Existing archive checksum mismatch')
    with zipfile.ZipFile(output) as z:
        for info in z.infolist():
            target=(root/info.filename).resolve()
            if not target.is_relative_to(root.resolve()):raise SystemExit('Unsafe archive path')
            if ((info.external_attr>>16)&0o170000)==0o120000:raise SystemExit('Symlink entry refused')
        z.extractall(root)
    print(json.dumps({'status':'PASS_TRANSPORT_AND_ARCHIVE_SHA256','archive_sha256':m['archive_sha256'],
                      'archive_bytes':m['archive_bytes'],'extracted_project':'MIRAGE-CAD'},indent=2))
    print('Next CPU-only check: python3 MIRAGE-CAD/tools/verify_revision_artifact.py')

if __name__=='__main__':main()
