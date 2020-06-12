import pytest
import os
from ingest import (
    should_ignore,
    is_safe_symlink,
    is_text_file,
    read_file_content,
    scan_directory,
    extract_files_content,
    create_file_content_string,
    create_summary_string,
    create_tree_structure,
    generate_token_string,
    ingest_single_file,
    ingest_from_query
)

# Test fixtures
@pytest.fixture
def sample_query():
    return {
        'user_name': 'test_user',
        'repo_name': 'test_repo',
        'local_path': '/tmp/test_repo',
        'subpath': '/',
        'branch': 'main',
        'commit': None,
        'max_file_size': 1000000,
        'slug': 'test_user/test_repo'
    }

@pytest.fixture
def temp_directory(tmp_path):
    # Create a temporary directory structure for testing
    test_dir = tmp_path / "test_repo"
    test_dir.mkdir()
    
    # Create some test files
    (test_dir / "file1.txt").write_text("Hello World")
    (test_dir / "file2.py").write_text("print('Hello')")
    
    # Create a subdirectory with files
    sub_dir = test_dir / "subdir"
    sub_dir.mkdir()
    (sub_dir / "file3.txt").write_text("Test content")
    
    return test_dir

def test_should_ignore():
    ignore_patterns = ['*.pyc', '__pycache__', '.git']
    
    assert should_ignore('test.pyc', '/base', ignore_patterns) == True
    assert should_ignore('main.py', '/base', ignore_patterns) == False
    assert should_ignore('__pycache__', '/base', ignore_patterns) == True

def test_is_safe_symlink(temp_directory):
    # Create a safe symlink within the temp directory
    safe_target = temp_directory / "file1.txt"
    safe_link = temp_directory / "safe_link"
    os.symlink(safe_target, safe_link)
    
    # Create an unsafe symlink pointing outside
    unsafe_link = temp_directory / "unsafe_link"
    os.symlink("/etc/passwd", unsafe_link)
    
    assert is_safe_symlink(str(safe_link), str(temp_directory)) == True
    assert is_safe_symlink(str(unsafe_link), str(temp_directory)) == False

def test_is_text_file(temp_directory):
    text_file = temp_directory / "file1.txt"
    
    assert is_text_file(str(text_file)) == True
    
    # Create a binary file
    binary_file = temp_directory / "binary.bin"
    with open(binary_file, 'wb') as f:
        f.write(bytes([0, 255, 254, 253]))
    
    assert is_text_file(str(binary_file)) == False

def test_read_file_content(temp_directory):
    test_file = temp_directory / "file1.txt"
    content = read_file_content(str(test_file))
    assert content == "Hello World"
    
    # Test with non-existent file
    assert "Error reading file" in read_file_content("nonexistent.txt")

def test_scan_directory(temp_directory):
    result = scan_directory(
        str(temp_directory),
        ignore_patterns=['*.pyc'],
        base_path=str(temp_directory)
    )
    
    assert result['type'] == 'directory'
    assert result['file_count'] == 3  # file1.txt, file2.py, subdir/file3.txt
    assert result['dir_count'] == 1   # subdir
    assert len(result['children']) == 3

def test_extract_files_content(temp_directory, sample_query):
    nodes = scan_directory(
        str(temp_directory),
        ignore_patterns=['*.pyc'],
        base_path=str(temp_directory)
    )
    
    files = extract_files_content(sample_query, nodes, max_file_size=1000000)
    assert len(files) == 3
    assert any(f['path'].endswith('file1.txt') for f in files)
    assert any(f['path'].endswith('file2.py') for f in files)
    assert any(f['path'].endswith('file3.txt') for f in files)

def test_create_file_content_string():
    files = [
        {'path': '/test/file1.txt', 'content': 'Hello', 'size': 5},
        {'path': '/test/file2.txt', 'content': 'World', 'size': 5}
    ]
    
    result = create_file_content_string(files)
    assert '=' * 48 in result
    assert 'file1.txt' in result
    assert 'file2.txt' in result
    assert 'Hello' in result
    assert 'World' in result

def test_create_summary_string(sample_query):
    nodes = {
        'file_count': 3,
        'dir_count': 1
    }
    files = [{'path': 'file1.txt', 'content': 'test', 'size': 4}]
    
    summary = create_summary_string(sample_query, nodes, files)
    assert 'test_user/test_repo' in summary
    assert 'Files analyzed: 3' in summary

def test_create_tree_structure(sample_query):
    node = {
        'name': 'root',
        'type': 'directory',
        'children': [
            {'name': 'file1.txt', 'type': 'file', 'children': []},
            {'name': 'subdir', 'type': 'directory', 'children': [
                {'name': 'file2.txt', 'type': 'file', 'children': []}
            ]}
        ]
    }
    
    tree = create_tree_structure(sample_query, node)
    assert '└── root' in tree
    assert '├── file1.txt' in tree
    assert '└── subdir' in tree
    assert 'file2.txt' in tree

def test_generate_token_string():
    small_text = "Hello World"
    large_text = "Hello " * 1000
    
    assert generate_token_string(small_text) is not None
    assert generate_token_string(large_text) is not None

def test_ingest_single_file(temp_directory, sample_query):
    test_file = temp_directory / "file1.txt"
    sample_query['local_path'] = str(temp_directory)
    
    summary, tree, content = ingest_single_file(str(test_file), sample_query)
    
    assert 'test_user/test_repo' in summary
    assert 'file1.txt' in tree
    assert 'Hello World' in content

def test_ingest_from_query(temp_directory, sample_query):
    sample_query['local_path'] = str(temp_directory)
    
    summary, tree, content = ingest_from_query(sample_query)
    
    assert 'test_user/test_repo' in summary
    assert 'file1.txt' in tree
    assert 'Hello World' in content 