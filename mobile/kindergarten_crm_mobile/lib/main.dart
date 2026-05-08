import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'api_client.dart';
import 'session.dart';

void main() {
  runApp(KindergartenCrmApp(apiClient: ApiClient()));
}

class KindergartenCrmApp extends StatefulWidget {
  const KindergartenCrmApp({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  State<KindergartenCrmApp> createState() => _KindergartenCrmAppState();
}

class _KindergartenCrmAppState extends State<KindergartenCrmApp> {
  late final AppSession session = AppSession(widget.apiClient);

  @override
  void initState() {
    super.initState();
    session.load();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: session,
      builder: (context, _) {
        return MaterialApp(
          title: 'Anvar Bogcha CRM',
          debugShowCheckedModeBanner: false,
          theme: ThemeData(
            colorScheme: ColorScheme.fromSeed(
              seedColor: const Color(0xff2f6ce5),
            ),
            useMaterial3: true,
            scaffoldBackgroundColor: const Color(0xfff7f9fc),
            cardTheme: const CardThemeData(
              elevation: 0,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.all(Radius.circular(18)),
              ),
            ),
            inputDecorationTheme: const InputDecorationTheme(
              border: OutlineInputBorder(
                borderRadius: BorderRadius.all(Radius.circular(14)),
              ),
            ),
          ),
          home: session.isLoading
              ? const SplashScreen()
              : session.isAuthenticated
              ? HomeScreen(session: session)
              : LoginScreen(session: session),
        );
      },
    );
  }
}

class SplashScreen extends StatelessWidget {
  const SplashScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(body: Center(child: CircularProgressIndicator()));
  }
}

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key, required this.session});

  final AppSession session;

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _username = TextEditingController();
  final _password = TextEditingController();
  bool _isSubmitting = false;
  String? _error;

  @override
  void dispose() {
    _username.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _isSubmitting = true;
      _error = null;
    });
    try {
      await widget.session.login(_username.text.trim(), _password.text);
    } on ApiException catch (error) {
      if (mounted) setState(() => _error = error.message);
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(22),
                  child: Form(
                    key: _formKey,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const _BrandHeader(subtitle: 'Tarbiyachi mobil paneli'),
                        const SizedBox(height: 22),
                        TextFormField(
                          controller: _username,
                          decoration: const InputDecoration(
                            labelText: 'Login',
                            prefixIcon: Icon(Icons.person_outline),
                          ),
                          textInputAction: TextInputAction.next,
                          validator: (value) =>
                              value == null || value.trim().isEmpty
                              ? 'Login kiriting'
                              : null,
                        ),
                        const SizedBox(height: 12),
                        TextFormField(
                          controller: _password,
                          decoration: const InputDecoration(
                            labelText: 'Parol',
                            prefixIcon: Icon(Icons.lock_outline),
                          ),
                          obscureText: true,
                          onFieldSubmitted: (_) => _submit(),
                          validator: (value) => value == null || value.isEmpty
                              ? 'Parol kiriting'
                              : null,
                        ),
                        if (_error != null) ...[
                          const SizedBox(height: 12),
                          Text(
                            _error!,
                            style: TextStyle(
                              color: Theme.of(context).colorScheme.error,
                            ),
                          ),
                        ],
                        const SizedBox(height: 18),
                        FilledButton(
                          onPressed: _isSubmitting ? null : _submit,
                          child: _isSubmitting
                              ? const SizedBox(
                                  width: 20,
                                  height: 20,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                  ),
                                )
                              : const Text('Kirish'),
                        ),
                        const SizedBox(height: 14),
                        Text(
                          'API: ${widget.session.api.baseUrl}',
                          textAlign: TextAlign.center,
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, required this.session});

  final AppSession session;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _index = const int.fromEnvironment('INITIAL_TAB', defaultValue: 0);

  @override
  Widget build(BuildContext context) {
    final destinations = <_Destination>[
      _Destination(
        'Dashboard',
        Icons.dashboard_outlined,
        DashboardPage(session: widget.session),
      ),
      _Destination(
        'Davomat',
        Icons.fact_check_outlined,
        AttendancePage(session: widget.session),
      ),
      _Destination(
        'Vasiylar',
        Icons.contact_phone_outlined,
        GuardiansPage(session: widget.session),
      ),
    ];

    return Scaffold(
      appBar: AppBar(
        title: Text(destinations[_index].label),
        actions: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8),
            child: Center(child: Text(widget.session.username)),
          ),
          IconButton(
            tooltip: 'Chiqish',
            onPressed: widget.session.logout,
            icon: const Icon(Icons.logout),
          ),
        ],
      ),
      body: destinations[_index].page,
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (value) => setState(() => _index = value),
        destinations: [
          for (final item in destinations)
            NavigationDestination(icon: Icon(item.icon), label: item.label),
        ],
      ),
    );
  }
}

class DashboardPage extends StatefulWidget {
  const DashboardPage({super.key, required this.session});

  final AppSession session;

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  late Future<Map<String, dynamic>> _future = widget.session.api.dashboard();

  Future<void> _refresh() async {
    setState(() => _future = widget.session.api.dashboard());
    await _future;
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Map<String, dynamic>>(
      future: _future,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return _ErrorState(
            message: snapshot.error.toString(),
            onRetry: _refresh,
          );
        }
        final data = snapshot.data!;
        final attendance = data['attendance'] as Map<String, dynamic>;
        final counts = data['counts'] as Map<String, dynamic>;
        final location = data['location'] as Map<String, dynamic>;
        return RefreshIndicator(
          onRefresh: _refresh,
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              const _BrandHeader(subtitle: 'Tarbiyachi dashboard'),
              const SizedBox(height: 16),
              _StatGrid(
                items: [
                  _StatItem(
                    'Keldi',
                    '${attendance['present']}',
                    Icons.check_circle_outline,
                  ),
                  _StatItem(
                    'Kechikdi',
                    '${attendance['late']}',
                    Icons.schedule_outlined,
                  ),
                  _StatItem(
                    'Kelmagan',
                    '${attendance['absent']}',
                    Icons.cancel_outlined,
                  ),
                  _StatItem(
                    'Vasiylar',
                    '${counts['guardians']}',
                    Icons.contact_phone_outlined,
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Card(
                child: ListTile(
                  leading: const Icon(Icons.groups_outlined),
                  title: Text("Faol bolalar: ${counts['active_children']}"),
                  subtitle: Text("Bugun: ${attendance['date']}"),
                ),
              ),
              Card(
                child: ListTile(
                  leading: const Icon(Icons.location_on_outlined),
                  title: Text(location['name']?.toString() ?? "Anvar Bog'cha"),
                  subtitle: Text(
                    (location['address']?.toString().isNotEmpty ?? false)
                        ? location['address'].toString()
                        : 'Joylashuv saqlanmagan',
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class AttendancePage extends StatefulWidget {
  const AttendancePage({super.key, required this.session});

  final AppSession session;

  @override
  State<AttendancePage> createState() => _AttendancePageState();
}

class _AttendancePageState extends State<AttendancePage> {
  final _search = TextEditingController();
  DateTime _date = DateTime.now();
  String _classroom = '';
  String _status = '';
  late Future<_AttendanceScreenData> _future = _load();

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  Future<_AttendanceScreenData> _load() async {
    final attendance = await widget.session.api.attendance(
      date: _date,
      classroom: _classroom,
      status: _status,
      query: _search.text,
    );
    final classrooms = await widget.session.api.classrooms();
    return _AttendanceScreenData(attendance, classrooms);
  }

  Future<void> _refresh() async {
    setState(() => _future = _load());
    await _future;
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _date,
      firstDate: DateTime(2020),
      lastDate: DateTime(2100),
    );
    if (picked != null) {
      setState(() {
        _date = picked;
        _future = _load();
      });
    }
  }

  Future<void> _mark(int id, String status) async {
    try {
      await widget.session.api.markAttendance(id, status);
      if (mounted) _showSnack(context, 'Davomat yangilandi.');
      await _refresh();
    } on ApiException catch (error) {
      if (mounted) _showSnack(context, error.message);
    }
  }

  Future<void> _bulkMarkPresent() async {
    if (_classroom.isEmpty) return;
    try {
      final data = await widget.session.api.bulkMarkPresent(
        date: _date,
        classroom: _classroom,
      );
      if (mounted) {
        _showSnack(context, '${data['updated']} ta bola keldi deb belgilandi.');
      }
      await _refresh();
    } on ApiException catch (error) {
      if (mounted) _showSnack(context, error.message);
    }
  }

  Future<void> _edit(
    Map<String, dynamic> row,
    List<Map<String, dynamic>> statuses,
  ) async {
    final changed = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      builder: (context) {
        return AttendanceEditSheet(
          api: widget.session.api,
          row: row,
          statuses: statuses,
        );
      },
    );
    if (changed == true) await _refresh();
  }

  void _applyFilters() {
    FocusManager.instance.primaryFocus?.unfocus();
    setState(() => _future = _load());
  }

  void _clearFilters() {
    _search.clear();
    setState(() {
      _classroom = '';
      _status = '';
      _future = _load();
    });
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<_AttendanceScreenData>(
      future: _future,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return _ErrorState(
            message: snapshot.error.toString(),
            onRetry: _refresh,
          );
        }
        final data = snapshot.data!;
        final attendance = data.attendance;
        final rows = (attendance['results'] as List)
            .cast<Map<String, dynamic>>();
        final summary = attendance['summary'] as Map<String, dynamic>;
        final statuses = (attendance['statuses'] as List)
            .cast<Map<String, dynamic>>();
        final classrooms = (data.classrooms['results'] as List)
            .cast<Map<String, dynamic>>();

        return RefreshIndicator(
          onRefresh: _refresh,
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              _AttendanceFilters(
                date: _date,
                classroom: _classroom,
                status: _status,
                search: _search,
                classrooms: classrooms,
                statuses: statuses,
                onPickDate: _pickDate,
                onClassroomChanged: (value) => setState(() {
                  _classroom = value ?? '';
                  _future = _load();
                }),
                onStatusChanged: (value) => setState(() {
                  _status = value ?? '';
                  _future = _load();
                }),
                onApply: _applyFilters,
                onClear: _clearFilters,
              ),
              const SizedBox(height: 12),
              _StatGrid(
                items: [
                  _StatItem(
                    'Keldi',
                    '${summary['present']}',
                    Icons.check_outlined,
                  ),
                  _StatItem(
                    'Kechikdi',
                    '${summary['late']}',
                    Icons.schedule_outlined,
                  ),
                  _StatItem(
                    'Kelmagan',
                    '${summary['absent']}',
                    Icons.cancel_outlined,
                  ),
                  _StatItem(
                    'Kutilmoqda',
                    '${summary['expected']}',
                    Icons.hourglass_empty,
                  ),
                ],
              ),
              if (_classroom.isNotEmpty) ...[
                const SizedBox(height: 12),
                FilledButton.icon(
                  onPressed: _bulkMarkPresent,
                  icon: const Icon(Icons.done_all),
                  label: const Text('Tanlangan guruhni keldi deb belgilash'),
                ),
              ],
              const SizedBox(height: 16),
              if (rows.isEmpty)
                const _EmptyState(text: 'Davomat yozuvlari topilmadi.')
              else
                for (final row in rows)
                  _AttendanceTile(
                    row: row,
                    onMark: _mark,
                    onEdit: () => _edit(row, statuses),
                  ),
            ],
          ),
        );
      },
    );
  }
}

class GuardiansPage extends StatefulWidget {
  const GuardiansPage({super.key, required this.session});

  final AppSession session;

  @override
  State<GuardiansPage> createState() => _GuardiansPageState();
}

class _GuardiansPageState extends State<GuardiansPage> {
  final _search = TextEditingController();
  late Future<Map<String, dynamic>> _future = _load();

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  Future<Map<String, dynamic>> _load() {
    return widget.session.api.guardians(query: _search.text);
  }

  Future<void> _refresh() async {
    setState(() => _future = _load());
    await _future;
  }

  void _applySearch() {
    FocusManager.instance.primaryFocus?.unfocus();
    setState(() => _future = _load());
  }

  void _clearSearch() {
    _search.clear();
    _applySearch();
  }

  Future<void> _copy(String value, String label) async {
    await Clipboard.setData(ClipboardData(text: value));
    if (mounted) _showSnack(context, '$label nusxalandi.');
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Map<String, dynamic>>(
      future: _future,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return _ErrorState(
            message: snapshot.error.toString(),
            onRetry: _refresh,
          );
        }
        final rows = (snapshot.data!['results'] as List)
            .cast<Map<String, dynamic>>();
        return RefreshIndicator(
          onRefresh: _refresh,
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _search,
                      decoration: const InputDecoration(
                        labelText: 'Vasiy yoki bola qidirish',
                        prefixIcon: Icon(Icons.search),
                      ),
                      textInputAction: TextInputAction.search,
                      onSubmitted: (_) => _applySearch(),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton.filledTonal(
                    onPressed: _applySearch,
                    icon: const Icon(Icons.search),
                  ),
                  IconButton(
                    onPressed: _clearSearch,
                    icon: const Icon(Icons.clear),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              if (rows.isEmpty)
                const _EmptyState(text: 'Vasiylar topilmadi.')
              else
                for (final row in rows)
                  _GuardianTile(
                    row: row,
                    onCopyPhone: () =>
                        _copy(row['phone'].toString(), 'Telefon'),
                    onCopyEmail: () => _copy(row['email'].toString(), 'Email'),
                  ),
            ],
          ),
        );
      },
    );
  }
}

class AttendanceEditSheet extends StatefulWidget {
  const AttendanceEditSheet({
    super.key,
    required this.api,
    required this.row,
    required this.statuses,
  });

  final ApiClient api;
  final Map<String, dynamic> row;
  final List<Map<String, dynamic>> statuses;

  @override
  State<AttendanceEditSheet> createState() => _AttendanceEditSheetState();
}

class _AttendanceEditSheetState extends State<AttendanceEditSheet> {
  final _formKey = GlobalKey<FormState>();
  late String _status = widget.row['status'].toString();
  late final TextEditingController _checkIn = TextEditingController(
    text: widget.row['check_in_time']?.toString() ?? '',
  );
  late final TextEditingController _checkOut = TextEditingController(
    text: widget.row['check_out_time']?.toString() ?? '',
  );
  late final TextEditingController _absenceReason = TextEditingController(
    text: widget.row['absence_reason']?.toString() ?? '',
  );
  late final TextEditingController _notes = TextEditingController(
    text: widget.row['notes']?.toString() ?? '',
  );
  bool _isSaving = false;
  String? _error;

  @override
  void dispose() {
    _checkIn.dispose();
    _checkOut.dispose();
    _absenceReason.dispose();
    _notes.dispose();
    super.dispose();
  }

  Future<void> _pickTime(TextEditingController controller) async {
    final picked = await showTimePicker(
      context: context,
      initialTime: _timeFromText(controller.text) ?? TimeOfDay.now(),
    );
    if (picked != null) {
      controller.text = _timeLabel(picked);
    }
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _isSaving = true;
      _error = null;
    });
    try {
      await widget.api.updateAttendance(widget.row['id'] as int, {
        'status': _status,
        'check_in_time': _checkIn.text.trim(),
        'check_out_time': _checkOut.text.trim(),
        'absence_reason': _absenceReason.text.trim(),
        'notes': _notes.text.trim(),
      });
      if (mounted) Navigator.of(context).pop(true);
    } on ApiException catch (error) {
      if (mounted) setState(() => _error = error.message);
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final child = widget.row['child'] as Map<String, dynamic>;
    return SafeArea(
      child: Padding(
        padding: EdgeInsets.only(
          left: 16,
          right: 16,
          top: 16,
          bottom: MediaQuery.of(context).viewInsets.bottom + 16,
        ),
        child: SingleChildScrollView(
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  child['full_name'].toString(),
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 14),
                DropdownButtonFormField<String>(
                  initialValue: _status,
                  decoration: const InputDecoration(labelText: 'Holat'),
                  items: [
                    for (final status in widget.statuses)
                      DropdownMenuItem(
                        value: status['value'].toString(),
                        child: Text(status['label'].toString()),
                      ),
                  ],
                  onChanged: (value) =>
                      setState(() => _status = value ?? _status),
                ),
                const SizedBox(height: 12),
                _TimeField(
                  controller: _checkIn,
                  label: 'Kirish vaqti',
                  onPick: () => _pickTime(_checkIn),
                ),
                const SizedBox(height: 12),
                _TimeField(
                  controller: _checkOut,
                  label: 'Chiqish vaqti',
                  onPick: () => _pickTime(_checkOut),
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _absenceReason,
                  minLines: 2,
                  maxLines: 4,
                  decoration: const InputDecoration(
                    labelText: 'Kelmagan sababi',
                  ),
                  validator: (value) =>
                      _status == 'absent' &&
                          (value == null || value.trim().isEmpty)
                      ? 'Kelmagan holati uchun sabab kiriting'
                      : null,
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _notes,
                  minLines: 2,
                  maxLines: 4,
                  decoration: const InputDecoration(labelText: 'Izoh'),
                ),
                if (_error != null) ...[
                  const SizedBox(height: 12),
                  Text(
                    _error!,
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.error,
                    ),
                  ),
                ],
                const SizedBox(height: 16),
                FilledButton(
                  onPressed: _isSaving ? null : _save,
                  child: _isSaving
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Saqlash'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _AttendanceFilters extends StatelessWidget {
  const _AttendanceFilters({
    required this.date,
    required this.classroom,
    required this.status,
    required this.search,
    required this.classrooms,
    required this.statuses,
    required this.onPickDate,
    required this.onClassroomChanged,
    required this.onStatusChanged,
    required this.onApply,
    required this.onClear,
  });

  final DateTime date;
  final String classroom;
  final String status;
  final TextEditingController search;
  final List<Map<String, dynamic>> classrooms;
  final List<Map<String, dynamic>> statuses;
  final VoidCallback onPickDate;
  final ValueChanged<String?> onClassroomChanged;
  final ValueChanged<String?> onStatusChanged;
  final VoidCallback onApply;
  final VoidCallback onClear;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          children: [
            OutlinedButton.icon(
              onPressed: onPickDate,
              icon: const Icon(Icons.today_outlined),
              label: Text(_dateLabel(date)),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              key: ValueKey('classroom-$classroom'),
              initialValue: classroom.isEmpty ? null : classroom,
              decoration: const InputDecoration(labelText: 'Guruh'),
              items: [
                const DropdownMenuItem(value: '', child: Text('Barchasi')),
                for (final item in classrooms)
                  DropdownMenuItem(
                    value: item['id'].toString(),
                    child: Text(item['name'].toString()),
                  ),
              ],
              onChanged: onClassroomChanged,
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              key: ValueKey('status-$status'),
              initialValue: status.isEmpty ? null : status,
              decoration: const InputDecoration(labelText: 'Holat'),
              items: [
                const DropdownMenuItem(value: '', child: Text('Barchasi')),
                for (final item in statuses)
                  DropdownMenuItem(
                    value: item['value'].toString(),
                    child: Text(item['label'].toString()),
                  ),
              ],
              onChanged: onStatusChanged,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: search,
              decoration: const InputDecoration(
                labelText: 'Bola qidirish',
                prefixIcon: Icon(Icons.search),
              ),
              textInputAction: TextInputAction.search,
              onSubmitted: (_) => onApply(),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: FilledButton.icon(
                    onPressed: onApply,
                    icon: const Icon(Icons.filter_alt_outlined),
                    label: const Text("Qo'llash"),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton.outlined(
                  tooltip: 'Tozalash',
                  onPressed: onClear,
                  icon: const Icon(Icons.clear),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _AttendanceTile extends StatelessWidget {
  const _AttendanceTile({
    required this.row,
    required this.onMark,
    required this.onEdit,
  });

  final Map<String, dynamic> row;
  final Future<void> Function(int id, String status) onMark;
  final VoidCallback onEdit;

  @override
  Widget build(BuildContext context) {
    final child = row['child'] as Map<String, dynamic>;
    final classroom = child['classroom'] as Map<String, dynamic>;
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        child['full_name'].toString(),
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      Text('${classroom['name']}  |  ${row['status_label']}'),
                    ],
                  ),
                ),
                IconButton(
                  tooltip: 'Tahrirlash',
                  onPressed: onEdit,
                  icon: const Icon(Icons.edit_outlined),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _InfoChip(
                  icon: Icons.login,
                  label: row['check_in_time']?.toString() ?? '-',
                ),
                _InfoChip(
                  icon: Icons.logout,
                  label: row['check_out_time']?.toString() ?? '-',
                ),
              ],
            ),
            if ((row['absence_reason']?.toString().isNotEmpty ?? false) ||
                (row['notes']?.toString().isNotEmpty ?? false)) ...[
              const SizedBox(height: 8),
              if (row['absence_reason']?.toString().isNotEmpty ?? false)
                Text('Sabab: ${row['absence_reason']}'),
              if (row['notes']?.toString().isNotEmpty ?? false)
                Text('Izoh: ${row['notes']}'),
            ],
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                ActionChip(
                  avatar: const Icon(Icons.check, size: 18),
                  label: const Text('Keldi'),
                  onPressed: () => onMark(row['id'] as int, 'present'),
                ),
                ActionChip(
                  avatar: const Icon(Icons.schedule, size: 18),
                  label: const Text('Kechikdi'),
                  onPressed: () => onMark(row['id'] as int, 'late'),
                ),
                ActionChip(
                  avatar: const Icon(Icons.close, size: 18),
                  label: const Text('Kelmagan'),
                  onPressed: () => onMark(row['id'] as int, 'absent'),
                ),
                ActionChip(
                  avatar: const Icon(Icons.timelapse, size: 18),
                  label: const Text('Yarim kun'),
                  onPressed: () => onMark(row['id'] as int, 'half_day'),
                ),
                ActionChip(
                  avatar: const Icon(Icons.restart_alt, size: 18),
                  label: const Text('Kutilmoqda'),
                  onPressed: () => onMark(row['id'] as int, 'expected'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _GuardianTile extends StatelessWidget {
  const _GuardianTile({
    required this.row,
    required this.onCopyPhone,
    required this.onCopyEmail,
  });

  final Map<String, dynamic> row;
  final VoidCallback onCopyPhone;
  final VoidCallback onCopyEmail;

  @override
  Widget build(BuildContext context) {
    final child = row['child'] as Map<String, dynamic>;
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    row['full_name'].toString(),
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                if (row['is_primary'] == true)
                  const Chip(label: Text('Asosiy')),
              ],
            ),
            Text('${child['full_name']}  |  ${child['classroom']}'),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(child: Text(row['phone'].toString())),
                IconButton(
                  tooltip: 'Telefonni nusxalash',
                  onPressed: onCopyPhone,
                  icon: const Icon(Icons.copy),
                ),
              ],
            ),
            Row(
              children: [
                Expanded(child: Text(row['email'].toString())),
                IconButton(
                  tooltip: 'Emailni nusxalash',
                  onPressed: onCopyEmail,
                  icon: const Icon(Icons.copy),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _TimeField extends StatelessWidget {
  const _TimeField({
    required this.controller,
    required this.label,
    required this.onPick,
  });

  final TextEditingController controller;
  final String label;
  final VoidCallback onPick;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: TextFormField(
            controller: controller,
            keyboardType: TextInputType.datetime,
            decoration: InputDecoration(labelText: label, hintText: 'HH:MM'),
            validator: (value) {
              final text = value?.trim() ?? '';
              if (text.isEmpty) return null;
              return RegExp(r'^\d{2}:\d{2}$').hasMatch(text)
                  ? null
                  : 'HH:MM formatida kiriting';
            },
          ),
        ),
        const SizedBox(width: 8),
        IconButton.filledTonal(
          tooltip: 'Vaqt tanlash',
          onPressed: onPick,
          icon: const Icon(Icons.access_time),
        ),
        IconButton(
          tooltip: 'Tozalash',
          onPressed: controller.clear,
          icon: const Icon(Icons.clear),
        ),
      ],
    );
  }
}

class _StatGrid extends StatelessWidget {
  const _StatGrid({required this.items});

  final List<_StatItem> items;

  @override
  Widget build(BuildContext context) {
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: 10,
      crossAxisSpacing: 10,
      childAspectRatio: 1.35,
      children: [
        for (final item in items)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Icon(item.icon),
                  Text(
                    item.value,
                    style: Theme.of(context).textTheme.headlineSmall,
                  ),
                  Text(
                    item.label,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
          ),
      ],
    );
  }
}

class _BrandHeader extends StatelessWidget {
  const _BrandHeader({required this.subtitle});

  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 48,
          height: 48,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            gradient: const LinearGradient(
              colors: [Color(0xffffcf54), Color(0xff55d6a7)],
            ),
          ),
          child: const Text(
            'A',
            style: TextStyle(fontSize: 22, fontWeight: FontWeight.w900),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                "Anvar Bog'cha",
                style: Theme.of(context).textTheme.titleLarge,
              ),
              Text(subtitle, style: Theme.of(context).textTheme.bodyMedium),
            ],
          ),
        ),
      ],
    );
  }
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({required this.message, required this.onRetry});

  final String message;
  final Future<void> Function() onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.cloud_off_outlined, size: 44),
            const SizedBox(height: 12),
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: 12),
            FilledButton.tonal(
              onPressed: onRetry,
              child: const Text('Qayta urinish'),
            ),
          ],
        ),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Center(child: Text(text)),
      ),
    );
  }
}

class _InfoChip extends StatelessWidget {
  const _InfoChip({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Chip(avatar: Icon(icon, size: 18), label: Text(label));
  }
}

class _AttendanceScreenData {
  const _AttendanceScreenData(this.attendance, this.classrooms);

  final Map<String, dynamic> attendance;
  final Map<String, dynamic> classrooms;
}

class _Destination {
  const _Destination(this.label, this.icon, this.page);

  final String label;
  final IconData icon;
  final Widget page;
}

class _StatItem {
  const _StatItem(this.label, this.value, this.icon);

  final String label;
  final String value;
  final IconData icon;
}

void _showSnack(BuildContext context, String message) {
  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
}

String _dateLabel(DateTime date) {
  final month = date.month.toString().padLeft(2, '0');
  final day = date.day.toString().padLeft(2, '0');
  return '${date.year}-$month-$day';
}

String _timeLabel(TimeOfDay time) {
  final hour = time.hour.toString().padLeft(2, '0');
  final minute = time.minute.toString().padLeft(2, '0');
  return '$hour:$minute';
}

TimeOfDay? _timeFromText(String text) {
  final parts = text.split(':');
  if (parts.length != 2) return null;
  final hour = int.tryParse(parts[0]);
  final minute = int.tryParse(parts[1]);
  if (hour == null || minute == null) return null;
  if (hour < 0 || hour > 23 || minute < 0 || minute > 59) return null;
  return TimeOfDay(hour: hour, minute: minute);
}
