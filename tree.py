import os
from pathlib import Path


def print_project_tree(start_path='.', ignore_list=None, max_depth=10, output_file=None):
    """
    Выводит структуру проекта в виде дерева
    """
    if ignore_list is None:
        ignore_list = [
            '__pycache__', '.pyc', '.git', '.venv', 'venv',
            '.idea', '.vscode', '.pytest_cache', '.mypy_cache',
            '*.egg-info', 'build', 'dist', 'migrations', 'typescript','node_modules'
        ]

    start_path = Path(start_path)
    output_lines = []

    def should_ignore(name):
        for pattern in ignore_list:
            if pattern.startswith('*') and name.endswith(pattern[1:]):
                return True
            if name == pattern:
                return True
        return False

    def build_tree(path, prefix="", is_last=True, depth=0):
        if depth > max_depth:
            return

        name = path.name if path != start_path else start_path.absolute().name
        if path != start_path and should_ignore(name):
            return

        # Текущий элемент
        if path == start_path:
            connector = ""
        else:
            connector = "└── " if is_last else "├── "

        line = f"{prefix}{connector}{name}"
        output_lines.append(line)

        if path.is_dir():
            try:
                # Получаем и сортируем содержимое
                items = list(path.iterdir())
                items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))

                # Фильтруем игнорируемые элементы
                items = [item for item in items if not should_ignore(item.name)]

                for index, item in enumerate(items):
                    is_last_item = index == len(items) - 1
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    build_tree(item, new_prefix, is_last_item, depth + 1)

            except PermissionError:
                output_lines.append(f"{prefix}    [Доступ запрещен]")

    # Строим дерево
    build_tree(start_path)

    # Выводим результат
    result = "\n".join(output_lines)
    print("Структура проекта:")
    print("=" * 50)
    print(result)

    # Сохраняем в файл если нужно
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("Структура проекта\n")
            f.write("=" * 50 + "\n")
            f.write(result + "\n")
        print(f"\nСтруктура сохранена в: {output_file}")

    return result


def get_project_stats():
    """Статистика проекта"""
    python_files = list(Path('.').rglob('*.py'))
    total_lines = 0
    total_files = len(python_files)

    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                total_lines += len(f.readlines())
        except:
            continue

    print(f"\nСтатистика Python файлов:")
    print(f"  Всего файлов: {total_files}")
    print(f"  Всего строк кода: {total_lines}")


if __name__ == "__main__":
    # Выводим структуру
    print_project_tree(output_file="project_structure.txt")

    # Показываем статистику
    get_project_stats()