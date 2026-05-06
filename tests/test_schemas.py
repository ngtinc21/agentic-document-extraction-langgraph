from pathlib import Path

from doc_extractor.io import load_job_file, load_source_documents

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_loads_esg_job_with_external_dictionary():
    job, base_dir = load_job_file(PROJECT_ROOT / "domains" / "esg" / "job.json")

    assert job.domain == "esg"
    assert job.entity.name == "Example Solar Ltd"
    assert len(job.dictionary) == 12
    assert base_dir.name == "esg"


def test_loads_synthetic_source_documents():
    job, base_dir = load_job_file(PROJECT_ROOT / "domains" / "esg" / "job.json")
    documents = load_source_documents(job, base_dir)

    assert len(documents) == 3
    assert all(document.content for document in documents)
