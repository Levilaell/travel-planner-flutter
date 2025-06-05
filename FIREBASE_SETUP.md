# Firebase Setup Guide

Este guia explica como configurar o Firebase como banco de dados para o aplicativo Travel Planner.

## 1. Criar Projeto Firebase

1. Acesse [Firebase Console](https://console.firebase.google.com/)
2. Clique em "Add project" ou "Adicionar projeto"
3. Escolha um nome para o projeto (ex: `travel-planner-app`)
4. Configure o Google Analytics (opcional)
5. Clique em "Create project"

## 2. Configurar Firebase para Android

1. No Firebase Console, clique em "Add app" > "Android"
2. Registre o app com package name: `com.example.frontend`
3. Baixe o arquivo `google-services.json`
4. Coloque o arquivo em `frontend/android/app/google-services.json`

## 3. Configurar Firebase para iOS

1. No Firebase Console, clique em "Add app" > "iOS"
2. Registre o app com bundle ID: `com.example.frontend`
3. Baixe o arquivo `GoogleService-Info.plist`
4. Coloque o arquivo em `frontend/ios/Runner/GoogleService-Info.plist`

## 4. Configurar Firestore Database

1. No Firebase Console, vá para "Firestore Database"
2. Clique em "Create database"
3. Escolha o modo "Test mode" (para desenvolvimento)
4. Selecione uma região próxima (ex: `southamerica-east1` para Brasil)

## 5. Configurar Authentication

1. No Firebase Console, vá para "Authentication"
2. Clique em "Get started"
3. Na aba "Sign-in method", habilite:
   - Email/Password
   - Google (opcional)

## 6. Configurar Service Account (Backend)

1. No Firebase Console, vá para "Project settings" > "Service accounts"
2. Clique em "Generate new private key"
3. Baixe o arquivo JSON
4. Renomeie para `credentials.json`
5. Coloque em `backend/config/credentials.json`

## 7. Atualizar Configurações

### Backend (.env)

Copie o arquivo `.env.example` para `.env` e configure:

```env
# Firebase Configuration
FIREBASE_API_KEY=your_firebase_api_key_here
FIREBASE_AUTH_DOMAIN=your_project_id.firebaseapp.com
FIREBASE_PROJECT_ID=your_project_id_here
FIREBASE_STORAGE_BUCKET=your_project_id.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your_messaging_sender_id_here
FIREBASE_APP_ID=your_firebase_app_id_here
USE_FIREBASE=True
```

Encontre esses valores em:
- Project settings > General > Your apps > Web app

### Frontend (firebase_options.dart)

Atualize o arquivo `frontend/lib/firebase_options.dart` com as configurações específicas do seu projeto:

1. Vá para Project settings > General
2. Copie as configurações para cada plataforma
3. Substitua os valores no arquivo

## 8. Instalar Dependências

### Backend
```bash
cd backend/
pip install -r requirements.txt
```

### Frontend
```bash
cd frontend/
flutter pub get
```

## 9. Regras de Segurança Firestore

Configure as regras em "Firestore Database" > "Rules":

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Usuários só podem acessar seus próprios dados
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Itinerários só podem ser acessados pelo proprietário
    match /itineraries/{itineraryId} {
      allow read, write: if request.auth != null && 
        request.auth.uid == resource.data.user;
    }
    
    // Dias só podem ser acessados se o usuário tem acesso ao itinerário
    match /days/{dayId} {
      allow read, write: if request.auth != null;
    }
    
    // Reviews só podem ser criadas por usuários autenticados
    match /reviews/{reviewId} {
      allow read: if true;
      allow write: if request.auth != null;
    }
  }
}
```

## 10. Executar a Aplicação

### Backend
```bash
cd backend/
python manage.py migrate  # Para sincronização híbrida
python manage.py runserver
```

### Frontend
```bash
cd frontend/
flutter run
```

## Estrutura de Dados no Firestore

### Collections:

1. **users**: Perfis de usuário
2. **itineraries**: Roteiros de viagem
3. **days**: Dias individuais dos roteiros
4. **reviews**: Avaliações dos roteiros

### Exemplo de Documento:

```json
{
  "itineraries": {
    "itinerary_id": {
      "user": "user_id",
      "destination": "Paris, França",
      "start_date": "2024-06-01",
      "end_date": "2024-06-07",
      "budget": 5000.00,
      "travelers": 2,
      "interests": "cultura, gastronomia",
      "generated_text": "...",
      "created_at": "2024-05-01T10:00:00Z"
    }
  }
}
```

## Migração de Dados (Opcional)

Se você já tem dados no SQLite, pode executar um script de migração:

```bash
cd backend/
python manage.py shell
>>> from itineraries.models import Itinerary
>>> for itinerary in Itinerary.objects.all():
...     itinerary.save_to_firestore()
```

## Troubleshooting

### Erro: "Default Firebase app has not been initialized"
- Verifique se o Firebase foi inicializado no main.dart
- Confirme se os arquivos de configuração estão nos locais corretos

### Erro: "PERMISSION_DENIED"
- Verifique as regras de segurança do Firestore
- Confirme se o usuário está autenticado

### Erro: "google-services.json not found"
- Baixe novamente o arquivo do Firebase Console
- Confirme se está no diretório correto (`android/app/`)

## Recursos Adicionais

- [Firebase Documentation](https://firebase.google.com/docs)
- [FlutterFire Documentation](https://firebase.flutter.dev/)
- [Firebase Admin Python SDK](https://firebase.google.com/docs/admin/setup)