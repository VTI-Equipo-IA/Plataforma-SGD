# -*- coding: utf-8 -*-
"""
Rutas para gestión de prompts del Agente Maestro
"""
from flask import render_template, request, jsonify, flash, redirect, url_for
from datetime import datetime
from . import prompts_bp
from services.prompt_service import PromptService
from extensions.csrf import csrf

prompt_service = PromptService()


@prompts_bp.route('/')
def index():
    """Vista principal de gestión de prompts"""
    try:
        # Obtener el prompt activo (más reciente)
        active_prompt = prompt_service.get_latest_prompt()
        
        # Obtener todas las versiones disponibles
        all_versions = prompt_service.get_all_prompts()
        
        return render_template(
            'prompts/index.html',
            active_prompt=active_prompt,
            all_versions=all_versions
        )
    except Exception as e:
        flash(f'Error al cargar prompts: {str(e)}', 'error')
        return render_template('prompts/index.html', active_prompt=None, all_versions=[])


@prompts_bp.route('/api/save', methods=['POST'])
@csrf.exempt
def save_prompt():
    """Guarda una nueva versión del prompt"""
    try:
        data = request.get_json()
        prompt_text = data.get('prompt', '').strip()
        version_label = data.get('version_label', '').strip()
        notas = data.get('notas', '').strip()
        
        if not prompt_text:
            return jsonify({'success': False, 'message': 'El prompt no puede estar vacío'}), 400
        
        # Generar etiqueta de versión si no se proporciona
        if not version_label:
            latest = prompt_service.get_latest_prompt()
            if latest and latest.get('version_label'):
                # Intentar incrementar versión (ej: v1.0 -> v1.1)
                try:
                    parts = latest['version_label'].replace('v', '').split('.')
                    if len(parts) >= 2:
                        major, minor = int(parts[0]), int(parts[1])
                        version_label = f'v{major}.{minor + 1}'
                    else:
                        version_label = 'v1.1'
                except:
                    version_label = f'v{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            else:
                version_label = 'v1.0'
        
        # Guardar nuevo prompt
        new_id = prompt_service.save_prompt(
            prompt_text=prompt_text,
            version_label=version_label,
            fuente='Editor Web',
            notas=notas or 'Editado manualmente desde la interfaz web'
        )
        
        return jsonify({
            'success': True,
            'message': f'Prompt guardado exitosamente como {version_label}',
            'id': new_id,
            'version_label': version_label
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error al guardar: {str(e)}'}), 500


@prompts_bp.route('/api/versions', methods=['GET'])
def get_versions():
    """Obtiene todas las versiones de prompts"""
    try:
        versions = prompt_service.get_all_prompts()
        return jsonify({'success': True, 'versions': versions})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error al obtener versiones: {str(e)}'}), 500


@prompts_bp.route('/api/version/<int:prompt_id>', methods=['GET'])
def get_version(prompt_id):
    """Obtiene una versión específica del prompt"""
    try:
        prompt = prompt_service.get_prompt_by_id(prompt_id)
        if not prompt:
            return jsonify({'success': False, 'message': 'Versión no encontrada'}), 404
        return jsonify({'success': True, 'prompt': prompt})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error al obtener versión: {str(e)}'}), 500


@prompts_bp.route('/api/restore/<int:prompt_id>', methods=['POST'])
@csrf.exempt
def restore_version(prompt_id):
    """Restaura una versión anterior del prompt (elimina versiones posteriores)"""
    try:
        # Verificar que la versión existe
        prompt = prompt_service.get_prompt_by_id(prompt_id)
        if not prompt:
            return jsonify({'success': False, 'message': 'Versión no encontrada'}), 404
        
        # Eliminar versiones posteriores
        deleted_count = prompt_service.delete_versions_after(prompt_id)
        
        return jsonify({
            'success': True,
            'message': f'Restaurado a versión {prompt.get("version_label", prompt_id)}',
            'deleted_count': deleted_count,
            'restored_id': prompt_id
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error al restaurar: {str(e)}'}), 500


@prompts_bp.route('/api/delete/<int:prompt_id>', methods=['DELETE'])
@csrf.exempt
def delete_version(prompt_id):
    """Elimina una versión específica del prompt (solo si no es la única)"""
    try:
        # Verificar que no sea la única versión
        all_prompts = prompt_service.get_all_prompts()
        if len(all_prompts) <= 1:
            return jsonify({
                'success': False,
                'message': 'No se puede eliminar la única versión disponible'
            }), 400
        
        # Eliminar
        success = prompt_service.delete_prompt(prompt_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Versión eliminada correctamente'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No se pudo eliminar la versión'
            }), 404
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error al eliminar: {str(e)}'}), 500
