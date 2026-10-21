import json, os, subprocess, sys, tempfile, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "jobs"))
import sample_heavy


class SampleJobTest(unittest.TestCase):
    def test_small_run_writes_summary(self):
        with tempfile.TemporaryDirectory() as d:
            s = sample_heavy.main(["--gb", "0.01", "--chunk-mb", "5", "--out", d])
            self.assertEqual(s["chunks"], 2)
            with open(os.path.join(d, "summary.json")) as f:
                self.assertEqual(json.load(f)["allocated_bytes"], s["allocated_bytes"])


class HelperTest(unittest.TestCase):
    def run_helper(self, *args, env_extra=None):
        env = {"PATH": os.environ.get("PATH", ""), **(env_extra or {})}
        return subprocess.run(["bash", os.path.join(ROOT, "offload_job.sh"), *args],
                              env=env, capture_output=True, text=True)

    def test_requires_repo(self):
        r = self.run_helper("sample_heavy")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("OFFLOAD_REPO", r.stderr)

    def test_rejects_bad_job_name(self):
        r = self.run_helper("../evil", env_extra={"OFFLOAD_REPO": "owner/repo"})
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
