from flask import Flask, render_template, request, jsonify
import re
import os
import json
import csv

app = Flask(__name__)

def load_tasks_from_csv():
    """Загружает задачи из CSV файла"""
    csv_file = '/home/asergeeva/Desktop/leetcode/web/tasks.csv'
    tasks = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Очищаем пробелы и преобразуем строки в числа для решений
                row['solution_1'] = int(row['solution_1'].strip()) if row['solution_1'].strip() else 0
                row['solution_2'] = int(row['solution_2'].strip()) if row['solution_2'].strip() else 0
                row['solution_3'] = int(row['solution_3'].strip()) if row['solution_3'].strip() else 0
                # Очищаем пробелы в других полях
                row['theme'] = row['theme'].strip() if row['theme'] else ''
                row['ideas'] = row['ideas'].strip() if row['ideas'] else ''
                tasks.append(row)
    except FileNotFoundError:
        print(f"Файл {csv_file} не найден")
    except Exception as e:
        print(f"Ошибка при чтении CSV файла: {e}")
    
    # Сортировка задач по сложности: Easy -> Medium -> Hard
    difficulty_order = {'Easy': 1, 'Medium': 2, 'Hard': 3}
    tasks.sort(key=lambda x: difficulty_order.get(x['difficulty'], 4))
    
    return tasks

def save_tasks_to_csv(tasks):
    """Сохраняет задачи в CSV файл"""
    csv_file = '/home/asergeeva/Desktop/leetcode/web/tasks.csv'
    try:
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ['number', 'title', 'difficulty', 'leetcode_link', 'theme', 'ideas', 'solution_1', 'solution_2', 'solution_3']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for task in tasks:
                writer.writerow(task)
        return True
    except Exception as e:
        print(f"Ошибка при сохранении CSV файла: {e}")
        return False

def get_solution_progress(task):
    """Вычисляет прогресс решения задачи (0-3)"""
    return task['solution_1'] + task['solution_2'] + task['solution_3']

def get_solution_percentage(task):
    """Вычисляет процент решения задачи (0-100)"""
    progress = get_solution_progress(task)
    return (progress / 3) * 100

@app.route('/')
def index():
    """Главная страница с таблицей задач"""
    tasks = load_tasks_from_csv()
    return render_template('index.html', tasks=tasks)

@app.route('/update_task', methods=['POST'])
def update_task():
    """Обновляет данные задачи в CSV"""
    data = request.get_json()
    task_number = data.get('task_number')
    field = data.get('field')
    value = data.get('value')
    
    try:
        # Загружаем все задачи
        tasks = load_tasks_from_csv()
        
        # Находим нужную задачу
        task_found = False
        for task in tasks:
            if task['number'] == task_number:
                task_found = True
                # Обновляем нужное поле
                if field in ['theme', 'ideas']:
                    task[field] = value
                elif field in ['solution_1', 'solution_2', 'solution_3']:
                    task[field] = int(value)
                break
        
        if not task_found:
            return jsonify({'success': False, 'message': f'Задача {task_number} не найдена'}), 404
        
        # Сохраняем обновленные задачи
        if save_tasks_to_csv(tasks):
            return jsonify({'success': True, 'message': f'Задача {task_number} обновлена'})
        else:
            return jsonify({'success': False, 'message': 'Ошибка при сохранении'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'}), 500

@app.route('/add_task', methods=['POST'])
def add_task():
    """Добавляет новую задачу в CSV"""
    data = request.get_json()
    title = data.get('title', '').strip()
    difficulty = data.get('difficulty', 'Easy').strip()
    leetcode_link = data.get('leetcode_link', '').strip()
    theme = data.get('theme', '').strip()
    ideas = data.get('ideas', '').strip()
    
    # Валидация
    if not title:
        return jsonify({'success': False, 'message': 'Название задачи обязательно'}), 400
    
    if difficulty not in ['Easy', 'Medium', 'Hard']:
        return jsonify({'success': False, 'message': 'Сложность должна быть Easy, Medium или Hard'}), 400
    
    try:
        # Загружаем все задачи
        tasks = load_tasks_from_csv()
        
        # Находим максимальный номер задачи
        max_number = 0
        for task in tasks:
            try:
                task_num = int(task['number'])
                if task_num > max_number:
                    max_number = task_num
            except (ValueError, TypeError):
                continue
        
        # Создаем новую задачу
        new_task = {
            'number': str(max_number + 1),
            'title': title,
            'difficulty': difficulty,
            'leetcode_link': leetcode_link,
            'theme': theme,
            'ideas': ideas,
            'solution_1': 0,
            'solution_2': 0,
            'solution_3': 0
        }
        
        # Добавляем задачу
        tasks.append(new_task)
        
        # Сортируем по сложности
        difficulty_order = {'Easy': 1, 'Medium': 2, 'Hard': 3}
        tasks.sort(key=lambda x: difficulty_order.get(x['difficulty'], 4))
        
        # Сохраняем
        if save_tasks_to_csv(tasks):
            return jsonify({
                'success': True, 
                'message': f'Задача "{title}" добавлена',
                'task': new_task
            })
        else:
            return jsonify({'success': False, 'message': 'Ошибка при сохранении'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'}), 500

@app.route('/delete_task', methods=['POST'])
def delete_task():
    """Удаляет задачу из CSV"""
    data = request.get_json()
    task_number = data.get('task_number')
    
    if not task_number:
        return jsonify({'success': False, 'message': 'Номер задачи обязателен'}), 400
    
    try:
        # Загружаем все задачи
        tasks = load_tasks_from_csv()
        
        # Находим и удаляем задачу
        task_found = False
        deleted_task = None
        for i, task in enumerate(tasks):
            if task['number'] == task_number:
                deleted_task = tasks.pop(i)
                task_found = True
                break
        
        if not task_found:
            return jsonify({'success': False, 'message': f'Задача {task_number} не найдена'}), 404
        
        # Сохраняем обновленные задачи
        if save_tasks_to_csv(tasks):
            return jsonify({
                'success': True, 
                'message': f'Задача "{deleted_task["title"]}" удалена',
                'deleted_task': deleted_task
            })
        else:
            return jsonify({'success': False, 'message': 'Ошибка при сохранении'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
