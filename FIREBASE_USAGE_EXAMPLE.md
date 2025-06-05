# Firebase Usage Examples

Este arquivo mostra como usar o Firebase Service no seu aplicativo Flutter.

## Importação

```dart
import 'package:frontend/services/firebase_service.dart';
import 'package:frontend/models/itinerary.dart';
import 'package:frontend/models/user.dart' as app_user;
```

## Autenticação

### Login com Email e Senha

```dart
Future<void> signIn(String email, String password) async {
  try {
    UserCredential? userCredential = await FirebaseService.signInWithEmailAndPassword(
      email, 
      password
    );
    
    if (userCredential != null) {
      print('Login successful: ${userCredential.user?.email}');
      // Navegar para a dashboard
    } else {
      print('Login failed');
    }
  } catch (e) {
    print('Error during login: $e');
  }
}
```

### Registrar Novo Usuário

```dart
Future<void> registerUser(String email, String password) async {
  try {
    UserCredential? userCredential = await FirebaseService.createUserWithEmailAndPassword(
      email, 
      password
    );
    
    if (userCredential != null) {
      print('Registration successful: ${userCredential.user?.email}');
      // Criar perfil do usuário
      await createUserProfile(userCredential.user!);
    }
  } catch (e) {
    print('Error during registration: $e');
  }
}
```

### Logout

```dart
Future<void> signOut() async {
  await FirebaseService.signOut();
  // Navegar para tela de login
}
```

## Gerenciamento de Perfil de Usuário

### Salvar Perfil

```dart
Future<void> createUserProfile(User firebaseUser) async {
  app_user.User userProfile = app_user.User(
    id: int.parse(firebaseUser.uid),
    username: firebaseUser.displayName ?? '',
    email: firebaseUser.email ?? '',
    dateJoined: DateTime.now(),
  );
  
  try {
    await FirebaseService.saveUserProfile(userProfile);
    print('User profile saved successfully');
  } catch (e) {
    print('Error saving user profile: $e');
  }
}
```

### Carregar Perfil

```dart
Future<app_user.User?> loadUserProfile(int userId) async {
  try {
    app_user.User? profile = await FirebaseService.getUserProfile(userId);
    if (profile != null) {
      print('Profile loaded: ${profile.username}');
      return profile;
    }
  } catch (e) {
    print('Error loading user profile: $e');
  }
  return null;
}
```

## Gerenciamento de Itinerários

### Salvar Itinerário

```dart
Future<void> saveItinerary(Itinerary itinerary) async {
  try {
    await FirebaseService.saveItinerary(itinerary);
    print('Itinerary saved successfully');
  } catch (e) {
    print('Error saving itinerary: $e');
  }
}
```

### Carregar Itinerários do Usuário

```dart
Future<List<Itinerary>> loadUserItineraries(int userId) async {
  try {
    List<Itinerary> itineraries = await FirebaseService.getUserItineraries(userId);
    print('Loaded ${itineraries.length} itineraries');
    return itineraries;
  } catch (e) {
    print('Error loading itineraries: $e');
    return [];
  }
}
```

### Carregar Itinerário Específico

```dart
Future<Itinerary?> loadItinerary(int itineraryId) async {
  try {
    Itinerary? itinerary = await FirebaseService.getItinerary(itineraryId);
    if (itinerary != null) {
      print('Itinerary loaded: ${itinerary.destination}');
    }
    return itinerary;
  } catch (e) {
    print('Error loading itinerary: $e');
    return null;
  }
}
```

### Deletar Itinerário

```dart
Future<void> deleteItinerary(int itineraryId) async {
  try {
    await FirebaseService.deleteItinerary(itineraryId);
    print('Itinerary deleted successfully');
  } catch (e) {
    print('Error deleting itinerary: $e');
  }
}
```

## Atualizações em Tempo Real

### Stream de Itinerários do Usuário

```dart
class DashboardScreen extends StatefulWidget {
  final int userId;
  
  const DashboardScreen({required this.userId});
  
  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: StreamBuilder<List<Itinerary>>(
        stream: FirebaseService.getUserItinerariesStream(widget.userId),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const CircularProgressIndicator();
          }
          
          if (snapshot.hasError) {
            return Text('Error: ${snapshot.error}');
          }
          
          if (!snapshot.hasData || snapshot.data!.isEmpty) {
            return const Text('No itineraries found');
          }
          
          List<Itinerary> itineraries = snapshot.data!;
          
          return ListView.builder(
            itemCount: itineraries.length,
            itemBuilder: (context, index) {
              Itinerary itinerary = itineraries[index];
              return ListTile(
                title: Text(itinerary.destination),
                subtitle: Text('${itinerary.startDate} - ${itinerary.endDate}'),
                onTap: () {
                  // Navegar para detalhes do itinerário
                },
              );
            },
          );
        },
      ),
    );
  }
}
```

### Stream de Itinerário Específico

```dart
class ItineraryDetailScreen extends StatelessWidget {
  final int itineraryId;
  
  const ItineraryDetailScreen({required this.itineraryId});
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Itinerary Details')),
      body: StreamBuilder<Itinerary?>(
        stream: FirebaseService.getItineraryStream(itineraryId),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const CircularProgressIndicator();
          }
          
          if (snapshot.hasError) {
            return Text('Error: ${snapshot.error}');
          }
          
          if (!snapshot.hasData) {
            return const Text('Itinerary not found');
          }
          
          Itinerary itinerary = snapshot.data!;
          
          return Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  itinerary.destination,
                  style: Theme.of(context).textTheme.headlineMedium,
                ),
                const SizedBox(height: 8),
                Text('${itinerary.startDate} - ${itinerary.endDate}'),
                const SizedBox(height: 16),
                Expanded(
                  child: SingleChildScrollView(
                    child: Text(itinerary.generatedText),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
```

## Operações em Lote

### Atualizar Múltiplos Itinerários

```dart
Future<void> batchUpdateItineraries(List<Itinerary> itineraries) async {
  try {
    await FirebaseService.batchUpdateItineraries(itineraries);
    print('Batch update completed successfully');
  } catch (e) {
    print('Error in batch update: $e');
  }
}
```

## Tratamento de Erros

```dart
Future<void> safeFirebaseOperation() async {
  try {
    // Sua operação Firebase aqui
    await FirebaseService.saveItinerary(itinerary);
  } on FirebaseException catch (e) {
    // Erros específicos do Firebase
    switch (e.code) {
      case 'permission-denied':
        print('Permission denied');
        break;
      case 'unavailable':
        print('Service unavailable');
        break;
      default:
        print('Firebase error: ${e.message}');
    }
  } catch (e) {
    // Outros erros
    print('General error: $e');
  }
}
```

## Inicialização no main.dart

```dart
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Inicializar Firebase
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );
  
  runApp(const MyApp());
}
```

## Provider Integration

```dart
import 'package:provider/provider.dart';

class ItineraryProvider extends ChangeNotifier {
  List<Itinerary> _itineraries = [];
  bool _isLoading = false;
  
  List<Itinerary> get itineraries => _itineraries;
  bool get isLoading => _isLoading;
  
  Future<void> loadItineraries(int userId) async {
    _isLoading = true;
    notifyListeners();
    
    try {
      _itineraries = await FirebaseService.getUserItineraries(userId);
    } catch (e) {
      print('Error loading itineraries: $e');
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
  
  Future<void> addItinerary(Itinerary itinerary) async {
    try {
      await FirebaseService.saveItinerary(itinerary);
      _itineraries.add(itinerary);
      notifyListeners();
    } catch (e) {
      print('Error adding itinerary: $e');
    }
  }
}

// No widget
Consumer<ItineraryProvider>(
  builder: (context, provider, child) {
    if (provider.isLoading) {
      return const CircularProgressIndicator();
    }
    
    return ListView.builder(
      itemCount: provider.itineraries.length,
      itemBuilder: (context, index) {
        // Build itinerary item
      },
    );
  },
)
```