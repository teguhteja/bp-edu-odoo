# Menjalankan Odoo untuk DB "labapp" dari worktree ini, terpisah dari container web utama.
#
# Pemakaian (PowerShell, dari root worktree):
#   .\labapp\odoo-labapp.ps1 serve                  # server di http://localhost:18070
#   .\labapp\odoo-labapp.ps1 run -i bp_edu_lab       # perintah odoo sekali jalan pada DB labapp
#   .\labapp\odoo-labapp.ps1 test                   # tes + tour di DB labapp_test (dibuat ulang)
#   .\labapp\odoo-labapp.ps1 shell labapp_import/import_labapp.py   # skrip di scripts/ via odoo shell
#
# Container tersambung ke network compose "odoo_app" sehingga host "db" = bp-edu-odoo_db_1.
# (Sengaja tanpa blok param(): argumen seperti -i/-u harus diteruskan apa adanya ke odoo.)
$Mode = if ($args.Count -gt 0) { $args[0] } else { 'serve' }
$Rest = @(if ($args.Count -gt 1) { $args[1..($args.Count - 1)] })

$Worktree = Split-Path -Parent $PSScriptRoot
$MainRepo = Join-Path (Split-Path -Parent $Worktree) 'bp-edu-odoo'
$Image = 'localhost/bp-edu-odoo-labapp:latest'
$Db = if ($env:LABAPP_DB) { $env:LABAPP_DB } else { 'labapp' }
$Modules = 'bp_edu_lab,bp_edu_lab_inventaris'

$Common = @(
    '--network', 'odoo_app',
    '-e', 'HOST=db', '-e', 'USER=odoo', '-e', 'PASSWORD=odoo',
    '-v', "$Worktree\addons:/mnt/extra-addons/addons:ro",
    '-v', "$MainRepo\third-party:/mnt/extra-addons/third-party:ro",
    '-v', "$MainRepo\config\odoo.conf:/etc/odoo/odoo.conf:ro",
    '-v', "$Worktree\scripts:/mnt/scripts:ro",
    '-v', 'bp-edu-odoo-labapp-filestore:/var/lib/odoo'
)

switch ($Mode) {
    'serve' {
        podman rm -f bp-edu-odoo_labapp 2>$null | Out-Null
        podman run -d --name bp-edu-odoo_labapp -p 18070:8069 @Common $Image `
            odoo -d $Db --db-filter "^$Db$" @Rest
    }
    'run' {
        podman run --rm @Common $Image odoo -d $Db --no-http --stop-after-init @Rest
    }
    'shell' {
        # Argumen = path skrip relatif terhadap folder scripts/, mis. labapp_import/import_labapp.py
        # (stdin dari pipeline PowerShell tidak sampai ke podman, jadi skrip dibaca di dalam container)
        $Script = $Rest[0]
        $ExtraEnv = @()
        if ($env:LABAPP_PASSWORD) { $ExtraEnv = @('-e', "LABAPP_PASSWORD=$($env:LABAPP_PASSWORD)") }
        podman run --rm @ExtraEnv @Common --entrypoint sh $Image -c `
            "odoo shell -d $Db --no-http --db_host db --db_user odoo --db_password odoo < /mnt/scripts/$Script"
    }
    'test' {
        $TestDb = 'labapp_test'
        podman exec bp-edu-odoo_db_1 dropdb -U odoo --if-exists --force $TestDb
        podman run --rm @Common $Image odoo -d $TestDb -i $Modules --test-enable `
            --test-tags "/bp_edu_lab,/bp_edu_lab_inventaris" --stop-after-init --http-port 8069 @Rest
    }
    default { throw "Mode tidak dikenal: $Mode (serve|run|shell|test)" }
}
