# Messageboard

Ein kleines Hobbyprojekt von mir. Es geht darum, ein Messageboard für z.B. ältere Leute zu erstellen, die kein Smartphone / Tablet mehr bedienen können / wollen und vielleicht auch nicht gerne telefonieren.

Auf der Website wird eine Board-ID eingegeben, mit der zwei HTML-Seiten erstellt werden. Die eine ist die Eingabemaske, die andere die Ausgabe. Die HTMLs werden im Azure BLOB abgelegt für effizientes und billiges Darstellen als Website. Bei einer Eingabe in der Eingabemaske wird eine Azure Function getriggert, die die Ausgabeseite neu erstellt.

Dem Empfänger kann man nun einen Raspberry Pi an z.B. einen Fernseher anschließen, der nur die Ausgabemaske anzeigt. So kann er/sie Nachrichten empfangen, ohne ein neues Gerät bedienen zu müssen.

Entstanden ist das ganze, weil in meiner Familie genau dieses Problem mit meinem Opa aufgetreten ist: er hat noch nie einen PC oder anderes technisches Gerät bedient und kann nur eingeschränkt telefonieren. Mit diesem Board können wir ihm nun auch mal kleinere Nachrichten schicken, ohne gleich vorbei fahren zu müssen - gerade in Corona-Zeiten sehr nützlich.