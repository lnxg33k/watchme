rule CMD : webshell
{
	meta:
		author		= "Ahmed Shawky"
		date		= "17, Jul 2017"
		description	= "Catch ASP web-shells"
	strings:
		$a = "cmd.exe" wide ascii nocase fullword
		$b = "xp_cmdshell" wide ascii nocase
	condition:
		any of them
}

rule ClassicASP : webshell
{
	meta:
		author		= "Ahmed Shawky"
		date		= "6, Mar 2018"
		description	= "Catch classic ASP web-shells with a different lang attr than C#"
	strings:
		$a = /eval\s*\(/	wide ascii nocase
		$b = /language\s*=\s*("|'|)\s*/ wide ascii nocase
		$c = /language\s*=\s*("|'|)\s*c#/ wide ascii nocase
		$d = /unsafe/ fullword ascii wide nocase
	condition:
		$a and ($b and not $c) and $d
}

rule NameSpaces : webshell
{
	meta:
		author		= "Ahmed Shawky"
		date		= "17, Jul 2017"
		description	= "Catch ASP(x) web-shells using common namespaces"
	strings:
		$a = "System.Diagnostics" wide ascii fullword
		$b = "System.Net.NetworkInformation" wide ascii fullword
		$c = "Microsoft.Management" wide ascii fullword
		$d = "System.Reflection" wide ascii fullword
		$e = "System.IO" wide ascii fullword
		$f = "System.Data.SqlClient" wide ascii fullword
	condition:
		any of them
}
