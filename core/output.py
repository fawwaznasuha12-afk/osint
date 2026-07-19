import json
import csv
from io import StringIO

class OutputFormatter:
    def to_text(self, data):
        output = []
        output.append("OSINT SCAN RESULTS")
        output.append("-" * 50)
        
        for module, results in data.get('results', {}).items():
            output.append(f"\n[{module.upper()}]")
            for key, value in results.items():
                if isinstance(value, list):
                    output.append(f"  {key}: {len(value)} items")
                elif isinstance(value, dict):
                    output.append(f"  {key}: {len(value)} entries")
                else:
                    output.append(f"  {key}: {value}")
                    
        return "\n".join(output)
        
    def to_csv(self, data):
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Module', 'Key', 'Value'])
        
        for module, results in data.get('results', {}).items():
            for key, value in results.items():
                if isinstance(value, list):
                    writer.writerow([module, key, len(value)])
                elif isinstance(value, dict):
                    writer.writerow([module, key, len(value)])
                else:
                    writer.writerow([module, key, value])
                    
        return output.getvalue()
