#!/usr/bin/env python3
"""
Script de monitoramento do Sistema de Gerenciamento de Alunos
"""
import os
import sys
import sqlite3
import requests
import psutil
from datetime import datetime
from pathlib import Path
import json

class SystemMonitor:
    def __init__(self):
        self.checks = []
        self.errors = []
        self.warnings = []
        
    def add_check(self, name, status, message, level="info"):
        """Adiciona um resultado de verificação"""
        check = {
            "name": name,
            "status": status,
            "message": message,
            "level": level,
            "timestamp": datetime.now().isoformat()
        }
        self.checks.append(check)
        
        if level == "error":
            self.errors.append(check)
        elif level == "warning":
            self.warnings.append(check)
    
    def check_database(self):
        """Verifica a saúde do banco de dados"""
        try:
            db_path = Path("instance/app.db")
            
            if not db_path.exists():
                self.add_check("Database", "ERROR", "Banco de dados não encontrado", "error")
                return
            
            # Verificar tamanho do banco
            size_mb = db_path.stat().st_size / (1024 * 1024)
            if size_mb > 100:  # Mais de 100MB
                self.add_check("Database Size", "WARNING", f"Banco de dados grande: {size_mb:.2f} MB", "warning")
            else:
                self.add_check("Database Size", "OK", f"Tamanho do banco: {size_mb:.2f} MB")
            
            # Verificar conectividade
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Verificar tabelas principais
            tables = ['users', 'students', 'lesson_types', 'payments', 'notifications', 'files']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                self.add_check(f"Table {table}", "OK", f"{count} registros")
            
            # Verificar integridade
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]
            if integrity == "ok":
                self.add_check("Database Integrity", "OK", "Integridade verificada")
            else:
                self.add_check("Database Integrity", "ERROR", f"Problemas de integridade: {integrity}", "error")
            
            conn.close()
            
        except Exception as e:
            self.add_check("Database", "ERROR", f"Erro ao verificar banco: {str(e)}", "error")
    
    def check_disk_space(self):
        """Verifica espaço em disco"""
        try:
            disk_usage = psutil.disk_usage('.')
            free_gb = disk_usage.free / (1024**3)
            used_percent = (disk_usage.used / disk_usage.total) * 100
            
            if free_gb < 1:  # Menos de 1GB livre
                self.add_check("Disk Space", "ERROR", f"Pouco espaço livre: {free_gb:.2f} GB", "error")
            elif free_gb < 5:  # Menos de 5GB livre
                self.add_check("Disk Space", "WARNING", f"Espaço livre baixo: {free_gb:.2f} GB", "warning")
            else:
                self.add_check("Disk Space", "OK", f"Espaço livre: {free_gb:.2f} GB ({used_percent:.1f}% usado)")
                
        except Exception as e:
            self.add_check("Disk Space", "ERROR", f"Erro ao verificar disco: {str(e)}", "error")
    
    def check_memory_usage(self):
        """Verifica uso de memória"""
        try:
            memory = psutil.virtual_memory()
            used_percent = memory.percent
            
            if used_percent > 90:
                self.add_check("Memory Usage", "ERROR", f"Uso de memória crítico: {used_percent:.1f}%", "error")
            elif used_percent > 80:
                self.add_check("Memory Usage", "WARNING", f"Uso de memória alto: {used_percent:.1f}%", "warning")
            else:
                self.add_check("Memory Usage", "OK", f"Uso de memória: {used_percent:.1f}%")
                
        except Exception as e:
            self.add_check("Memory Usage", "ERROR", f"Erro ao verificar memória: {str(e)}", "error")
    
    def check_backups(self):
        """Verifica backups recentes"""
        try:
            backup_dir = Path("backups")
            
            if not backup_dir.exists():
                self.add_check("Backups", "WARNING", "Diretório de backups não encontrado", "warning")
                return
            
            backup_files = list(backup_dir.glob("backup_*.db"))
            
            if not backup_files:
                self.add_check("Backups", "WARNING", "Nenhum backup encontrado", "warning")
                return
            
            # Verificar backup mais recente
            latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
            backup_age = datetime.now().timestamp() - latest_backup.stat().st_mtime
            backup_age_hours = backup_age / 3600
            
            if backup_age_hours > 24:
                self.add_check("Backups", "WARNING", f"Último backup há {backup_age_hours:.1f} horas", "warning")
            else:
                self.add_check("Backups", "OK", f"Último backup há {backup_age_hours:.1f} horas")
            
            # Verificar número de backups
            if len(backup_files) < 3:
                self.add_check("Backup Count", "WARNING", f"Apenas {len(backup_files)} backups disponíveis", "warning")
            else:
                self.add_check("Backup Count", "OK", f"{len(backup_files)} backups disponíveis")
                
        except Exception as e:
            self.add_check("Backups", "ERROR", f"Erro ao verificar backups: {str(e)}", "error")
    
    def check_logs(self):
        """Verifica logs do sistema"""
        try:
            log_dir = Path("logs")
            
            if not log_dir.exists():
                self.add_check("Logs", "WARNING", "Diretório de logs não encontrado", "warning")
                return
            
            # Verificar tamanho dos logs
            total_size = 0
            for log_file in log_dir.glob("*.log"):
                total_size += log_file.stat().st_size
            
            total_size_mb = total_size / (1024 * 1024)
            
            if total_size_mb > 100:  # Mais de 100MB de logs
                self.add_check("Log Size", "WARNING", f"Logs muito grandes: {total_size_mb:.2f} MB", "warning")
            else:
                self.add_check("Log Size", "OK", f"Tamanho dos logs: {total_size_mb:.2f} MB")
                
        except Exception as e:
            self.add_check("Logs", "ERROR", f"Erro ao verificar logs: {str(e)}", "error")
    
    def check_application_status(self):
        """Verifica se a aplicação está respondendo"""
        try:
            # Tentar conectar na aplicação
            response = requests.get("http://127.0.0.1:5000/", timeout=5)
            
            if response.status_code == 200:
                self.add_check("Application Status", "OK", "Aplicação respondendo normalmente")
            else:
                self.add_check("Application Status", "WARNING", f"Aplicação retornou status {response.status_code}", "warning")
                
        except requests.exceptions.ConnectionError:
            self.add_check("Application Status", "ERROR", "Aplicação não está rodando", "error")
        except Exception as e:
            self.add_check("Application Status", "ERROR", f"Erro ao verificar aplicação: {str(e)}", "error")
    
    def run_all_checks(self):
        """Executa todas as verificações"""
        print("🔍 Iniciando verificação do sistema...")
        print("=" * 50)
        
        self.check_database()
        self.check_disk_space()
        self.check_memory_usage()
        self.check_backups()
        self.check_logs()
        self.check_application_status()
        
        # Exibir resultados
        print("\n📊 Resultados da Verificação:")
        print("=" * 50)
        
        for check in self.checks:
            status_icon = {
                "OK": "✅",
                "WARNING": "⚠️",
                "ERROR": "❌"
            }.get(check["status"], "❓")
            
            print(f"{status_icon} {check['name']}: {check['message']}")
        
        # Resumo
        print("\n" + "=" * 50)
        print(f"📈 Total de verificações: {len(self.checks)}")
        print(f"✅ Sucessos: {len(self.checks) - len(self.warnings) - len(self.errors)}")
        print(f"⚠️  Avisos: {len(self.warnings)}")
        print(f"❌ Erros: {len(self.errors)}")
        
        if self.errors:
            print("\n🚨 ERROS CRÍTICOS ENCONTRADOS:")
            for error in self.errors:
                print(f"  - {error['name']}: {error['message']}")
        
        if self.warnings:
            print("\n⚠️  AVISOS:")
            for warning in self.warnings:
                print(f"  - {warning['name']}: {warning['message']}")
        
        # Retornar código de saída apropriado
        if self.errors:
            return 2  # Erro crítico
        elif self.warnings:
            return 1  # Aviso
        else:
            return 0  # Tudo OK
    
    def export_json(self, filename="monitor_report.json"):
        """Exporta relatório em JSON"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "checks": self.checks,
            "summary": {
                "total": len(self.checks),
                "success": len(self.checks) - len(self.warnings) - len(self.errors),
                "warnings": len(self.warnings),
                "errors": len(self.errors)
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Relatório exportado para: {filename}")

def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor do Sistema de Gerenciamento de Alunos")
    parser.add_argument("--json", help="Exportar relatório em JSON")
    parser.add_argument("--quiet", action="store_true", help="Modo silencioso")
    
    args = parser.parse_args()
    
    monitor = SystemMonitor()
    exit_code = monitor.run_all_checks()
    
    if args.json:
        monitor.export_json(args.json)
    
    if args.quiet:
        return exit_code
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main()) 