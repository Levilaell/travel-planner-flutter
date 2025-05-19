// lib/main.dart

import 'package:flutter/material.dart';
import 'screens/login_screen.dart';
import 'screens/register_screen.dart';
import 'screens/dashboard_screen.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Plantrip.ai',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        primarySwatch: Colors.deepPurple,
        scaffoldBackgroundColor: const Color(0xFFF7F7F7),
        inputDecorationTheme: const InputDecorationTheme(border: OutlineInputBorder()),
      ),
      initialRoute: '/',
      routes: {
        '/':         (_) => const LoginScreen(),
        '/register': (_) => const RegisterScreen(),
        '/dashboard': (ctx) {
          final token = ModalRoute.of(ctx)!.settings.arguments as String;
          return DashboardScreen(token: token);
        },
      },
    );
  }
}
