"""Focused safeguards for exact copying and immutable-source mappings."""
import tempfile
import unittest
from pathlib import Path
from archive_raw_evidence import add_source, copy_exact, sha, ROOT


class RawArchiveTests(unittest.TestCase):
    def item(self,path="/original/a.txt",digest="a"*64):
        return {"path":path,"sha256":digest,"bytes":12}

    def test_same_source_retains_multiple_roles(self):
        m={}
        add_source(m,self.item(),"first")
        add_source(m,self.item(),"second")
        self.assertEqual(m["/original/a.txt"]["roles"],["first","second"])

    def test_changed_source_is_rejected(self):
        m={}
        add_source(m,self.item(),"first")
        with self.assertRaises(ValueError):
            add_source(m,self.item(digest="b"*64),"second")

    def test_identical_bytes_share_object(self):
        m={}
        add_source(m,self.item(),"first")
        add_source(m,self.item(path="/another/a.txt"),"second")
        self.assertEqual(len({r["archive_path"] for r in m.values()}),1)

    def test_copy_preserves_exact_whitespace_and_bytes(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp:
            a,b=Path(temp)/"a",Path(temp)/"b"
            data=b"\xef\xbb\xbf   original\r\n\n\x00\xff"
            a.write_bytes(data)
            copy_exact(a,b,sha(a))
            self.assertEqual(b.read_bytes(),data)
            self.assertEqual(a.read_bytes(),data)

    def test_existing_destination_not_overwritten(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp:
            a,b=Path(temp)/"a",Path(temp)/"b"
            a.write_bytes(b"source")
            b.write_bytes(b"manual content")
            with self.assertRaises(ValueError):
                copy_exact(a,b,sha(a))
            self.assertEqual(b.read_bytes(),b"manual content")

    def test_bad_hash_is_rejected(self):
        with self.assertRaises(ValueError):
            add_source({},self.item(digest="../bad"),"first")


if __name__=="__main__":
    unittest.main()
