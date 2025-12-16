"""
Multi-Project Basecamp Webhook Setup Script
Registers ONE webhook endpoint for ALL projects
"""

import requests
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
CONFIG = {
    'CLIENT_ID': os.getenv('CLIENT_ID', ''),
    'CLIENT_SECRET': os.getenv('CLIENT_SECRET', ''),
    'REFRESH_TOKEN': os.getenv('REFRESH_TOKEN', ''),
    'ACCOUNT_ID': os.getenv('ACCOUNT_ID', ''),
}

# All projects that need webhook
PROJECTS = [
    37749144,  # ABAD BUILDERS
    42909637,  # ActivBase
    32745257,  # Angel Lungies
    43383165,  # Bismi Connect
    36261272,  # Brillar
    30438693,  # BluCampus
    24763032,  # BluSteak
    24763639,  # Care N cure
    42155802,  # Chakolas
    44872946,  # Dito
    33660253,  # Geojit
    43774549,  # Green Oasis
    43475806,  # Halwa Haweli
    44358469,  # Happy Hens
    40447220,  # Incheon Kia
    42358027,  # Little Bites
    43584998,  # Me n Moms
    36248868,  # MeronKart
    44319946,  # Mother's Food
    44944277,  # Pulimoottil
    34803430,  # Zeiq Consultants
]

def get_token():
    """Get fresh Basecamp access token"""
    print("🔑 Getting access token...")
    
    response = requests.post(
        'https://launchpad.37signals.com/authorization/token',
        data={
            'type': 'refresh',
            'client_id': CONFIG['CLIENT_ID'],
            'client_secret': CONFIG['CLIENT_SECRET'],
            'refresh_token': CONFIG['REFRESH_TOKEN']
        },
        headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'blusteak QC Bot (operations@blusteak.com)'
        }
    )
    
    response.raise_for_status()
    token = response.json()['access_token']
    print("✅ Token obtained!\n")
    return token

def list_webhooks(token, project_id):
    """List all existing webhooks for a project"""
    url = f'https://3.basecampapi.com/{CONFIG["ACCOUNT_ID"]}/buckets/{project_id}/webhooks.json'
    
    response = requests.get(
        url,
        headers={
            'Authorization': f'Bearer {token}',
            'User-Agent': 'blusteak QC Bot (operations@blusteak.com)'
        }
    )
    
    if response.ok:
        return response.json()
    return []

def delete_webhook(token, project_id, webhook_id):
    """Delete a specific webhook"""
    url = f'https://3.basecampapi.com/{CONFIG["ACCOUNT_ID"]}/buckets/{project_id}/webhooks/{webhook_id}.json'
    
    response = requests.delete(
        url,
        headers={
            'Authorization': f'Bearer {token}',
            'User-Agent': 'blusteak QC Bot (operations@blusteak.com)'
        }
    )
    
    return response.ok or response.status_code == 204

def create_webhook(token, project_id, ngrok_url):
    """Create new webhook for a project"""
    url = f'https://3.basecampapi.com/{CONFIG["ACCOUNT_ID"]}/buckets/{project_id}/webhooks.json'
    
    response = requests.post(
        url,
        json={
            'payload_url': f'{ngrok_url}/webhook/basecamp',
            'types': ['Comment']
        },
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'User-Agent': 'blusteak QC Bot (operations@blusteak.com)'
        }
    )
    
    if response.ok:
        webhook = response.json()
        return True, webhook
    else:
        return False, response.text

def main():
    """Main setup function"""
    print("\n" + "="*60)
    print("🤖 MULTI-PROJECT WEBHOOK SETUP")
    print("="*60 + "\n")
    
    # Get ngrok URL from user
    if len(sys.argv) > 1:
        ngrok_url = sys.argv[1].rstrip('/')
    else:
        print("Enter your ngrok URL (e.g., https://abc123.ngrok-free.app):")
        ngrok_url = input("> ").strip().rstrip('/')
    
    if not ngrok_url.startswith('http'):
        print("❌ Invalid URL. Must start with http:// or https://")
        return
    
    print(f"\n🎯 Target URL: {ngrok_url}/webhook/basecamp")
    print(f"📋 Projects to configure: {len(PROJECTS)}\n")
    
    try:
        # Get token
        token = get_token()
        
        # Ask if should delete old webhooks
        print("⚠️  Delete all existing webhooks before creating new ones? (y/n)")
        should_delete = input("> ").strip().lower() == 'y'
        print()
        
        success_count = 0
        failed_projects = []
        
        for i, project_id in enumerate(PROJECTS, 1):
            print(f"[{i}/{len(PROJECTS)}] Project ID: {project_id}")
            print("-" * 40)
            
            try:
                # List existing webhooks
                existing = list_webhooks(token, project_id)
                
                if existing:
                    print(f"  Found {len(existing)} existing webhook(s)")
                    
                    if should_delete:
                        for webhook in existing:
                            if delete_webhook(token, project_id, webhook['id']):
                                print(f"  🗑️  Deleted webhook {webhook['id']}")
                            else:
                                print(f"  ⚠️  Failed to delete {webhook['id']}")
                
                # Create new webhook
                success, result = create_webhook(token, project_id, ngrok_url)
                
                if success:
                    print(f"  ✅ Webhook created! ID: {result['id']}")
                    success_count += 1
                else:
                    print(f"  ❌ Failed: {result[:100]}")
                    failed_projects.append(project_id)
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
                failed_projects.append(project_id)
            
            print()
        
        # Summary
        print("="*60)
        print("📊 SETUP SUMMARY")
        print("="*60)
        print(f"✅ Successful: {success_count}/{len(PROJECTS)}")
        
        if failed_projects:
            print(f"❌ Failed: {len(failed_projects)}")
            print(f"   Project IDs: {failed_projects}")
        
        if success_count == len(PROJECTS):
            print("\n🎉 ALL WEBHOOKS CONFIGURED SUCCESSFULLY!")
            print("\n📝 Next steps:")
            print("1. Go to any configured Basecamp project")
            print("2. Add a comment with @nokk")
            print("3. Bot will auto-detect project and apply brand context")
            print("4. Watch the magic happen! ✨\n")
        else:
            print("\n⚠️  Some webhooks failed. Check errors above.")
        
        print("="*60 + "\n")
    
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}\n")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()