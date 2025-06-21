#!/usr/bin/env python3
"""
Script de backup automático do banco de dados
"""
import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

def create_backup():
    """Cria backup do banco de dados"""
    try:
        # Configurar caminhos
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        
        # Caminho do banco de dados
        db_path = Path("instance/app.db")
        
        if not db_path.exists():
            print("❌ Banco de dados não encontrado!")
            return False
        
        # Nome do arquivo de backup com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{timestamp}.db"
        backup_path = backup_dir / backup_filename
        
        # Criar backup
        shutil.copy2(db_path, backup_path)
        
        # Verificar se o backup foi criado
        if backup_path.exists():
            # Obter tamanho do arquivo
            size_mb = backup_path.stat().st_size / (1024 * 1024)
            print(f"✅ Backup criado: {backup_filename} ({size_mb:.2f} MB)")
            
            # Limpar backups antigos (manter apenas os últimos 10)
            cleanup_old_backups(backup_dir, max_backups=10)
            
            return True
        else:
            print("❌ Falha ao criar backup!")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao criar backup: {e}")
        return False

def cleanup_old_backups(backup_dir, max_backups=10):
    """Remove backups antigos, mantendo apenas os mais recentes"""
    try:
        # Listar todos os arquivos de backup
        backup_files = list(backup_dir.glob("backup_*.db"))
        
        if len(backup_files) > max_backups:
            # Ordenar por data de modificação (mais antigos primeiro)
            backup_files.sort(key=lambda x: x.stat().st_mtime)
            
            # Remover os mais antigos
            files_to_remove = backup_files[:-max_backups]
            
            for file in files_to_remove:
                file.unlink()
                print(f"🗑️  Backup removido: {file.name}")
                
    except Exception as e:
        print(f"⚠️  Erro ao limpar backups antigos: {e}")

def verify_backup(backup_path):
    """Verifica se o backup é válido"""
    try:
        # Tentar conectar ao banco de backup
        conn = sqlite3.connect(backup_path)
        cursor = conn.cursor()
        
        # Verificar se as tabelas principais existem
        tables = ['users', 'students', 'lesson_types', 'payments', 'notifications', 'files']
        
        for table in tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not cursor.fetchone():
                print(f"⚠️  Tabela '{table}' não encontrada no backup")
                return False
        
        conn.close()
        print("✅ Backup verificado com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar backup: {e}")
        return False

def list_backups():
    """Lista todos os backups disponíveis"""
    backup_dir = Path("backups")
    
    if not backup_dir.exists():
        print("📁 Nenhum backup encontrado")
        return
    
    backup_files = list(backup_dir.glob("backup_*.db"))
    
    if not backup_files:
        print("📁 Nenhum backup encontrado")
        return
    
    print("📋 Backups disponíveis:")
    print("-" * 60)
    
    for file in sorted(backup_files, key=lambda x: x.stat().st_mtime, reverse=True):
        size_mb = file.stat().st_size / (1024 * 1024)
        mod_time = datetime.fromtimestamp(file.stat().st_mtime)
        print(f"📄 {file.name}")
        print(f"   Tamanho: {size_mb:.2f} MB")
        print(f"   Data: {mod_time.strftime('%d/%m/%Y %H:%M:%S')}")
        print()

def restore_backup(backup_filename):
    """Restaura um backup específico"""
    try:
        backup_path = Path("backups") / backup_filename
        
        if not backup_path.exists():
            print(f"❌ Backup não encontrado: {backup_filename}")
            return False
        
        # Verificar se o backup é válido
        if not verify_backup(backup_path):
            print("❌ Backup inválido!")
            return False
        
        # Fazer backup do banco atual antes de restaurar
        current_db = Path("instance/app.db")
        if current_db.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safety_backup = Path("backups") / f"pre_restore_{timestamp}.db"
            shutil.copy2(current_db, safety_backup)
            print(f"🛡️  Backup de segurança criado: {safety_backup.name}")
        
        # Restaurar backup
        shutil.copy2(backup_path, current_db)
        print(f"✅ Backup restaurado: {backup_filename}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao restaurar backup: {e}")
        return False

def main():
    """Função principal"""
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python backup_db.py <comando>")
        print("Comandos disponíveis:")
        print("  create   - Criar novo backup")
        print("  list     - Listar backups disponíveis")
        print("  restore <arquivo> - Restaurar backup específico")
        print("  verify <arquivo>  - Verificar backup específico")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "create":
        create_backup()
        
    elif command == "list":
        list_backups()
        
    elif command == "restore":
        if len(sys.argv) < 3:
            print("❌ Especifique o arquivo de backup para restaurar")
            sys.exit(1)
        restore_backup(sys.argv[2])
        
    elif command == "verify":
        if len(sys.argv) < 3:
            print("❌ Especifique o arquivo de backup para verificar")
            sys.exit(1)
        backup_path = Path("backups") / sys.argv[2]
        verify_backup(backup_path)
        
    else:
        print(f"❌ Comando desconhecido: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main() 