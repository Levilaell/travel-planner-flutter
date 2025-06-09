#!/bin/bash

# Script para iniciar o projeto em qualquer rede

echo "🚀 Iniciando Travel Planner..."

# Definir diretório base
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "📂 Diretório base: $BASE_DIR"

# Detectar IP da máquina (compatível com macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | grep -v "inet6" | awk '{print $2}' | head -1)
else
    # Linux
    IP=$(hostname -I | awk '{print $1}')
fi

# Fallback para localhost se não encontrar IP
if [ -z "$IP" ]; then
    IP="localhost"
fi

echo "📍 IP detectado: $IP"

# Matar processos anteriores na porta 3000
echo "🧹 Limpando portas..."
lsof -ti:3000 | xargs kill -9 2>/dev/null
lsof -ti:8000 | xargs kill -9 2>/dev/null

# Atualizar .env do backend
cd "$BASE_DIR/backend"
sed -i.bak "s/ALLOWED_HOSTS=.*/ALLOWED_HOSTS=127.0.0.1,localhost,$IP/" .env
echo "✅ Backend .env atualizado"

# Atualizar arquivos Flutter
cd "$BASE_DIR/frontend/lib/services"
sed -i.bak "s|http://[0-9.]*:8000|http://$IP:8000|g" auth_service.dart
sed -i.bak "s|http://[0-9.]*:8000|http://$IP:8000|g" itinerary_service.dart
sed -i.bak "s|http://[0-9.]*:8000|http://$IP:8000|g" ../screens/create_itinerary_screen.dart
echo "✅ Flutter atualizado com novo IP"

# Iniciar backend
cd "$BASE_DIR/backend"
echo "🔧 Iniciando backend Django em $IP:8000..."
python manage.py runserver $IP:8000 &
BACKEND_PID=$!

# Aguardar backend iniciar
sleep 5

# Limpar e preparar Flutter
cd "$BASE_DIR/frontend"
echo "🧹 Limpando cache do Flutter..."
flutter clean > /dev/null 2>&1
flutter pub get > /dev/null 2>&1

# Iniciar frontend
echo "🎨 Iniciando Flutter web..."
flutter run -d chrome --web-port=3000 --web-hostname=0.0.0.0 &
FLUTTER_PID=$!

echo ""
echo "✅ Aplicação iniciada!"
echo "📱 No celular, acesse: http://$IP:3000"
echo "💻 No computador, acesse: http://localhost:3000"
echo ""
echo "Para parar, pressione Ctrl+C"

# Função para limpar ao sair
cleanup() {
    echo ""
    echo "🛑 Parando aplicação..."
    kill $BACKEND_PID 2>/dev/null
    kill $FLUTTER_PID 2>/dev/null
    exit 0
}

# Capturar Ctrl+C
trap cleanup INT

# Aguardar
wait