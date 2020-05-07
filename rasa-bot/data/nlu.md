## intent:greet
- hey
- hei
- Salut
- bună

## intent:goodbye
- bye
- pa
- pa pa
- mersi
- gata
- super

## intent:affirm
- da
- dap
- sigur
- pare ok
- corect

## intent:deny
- nu
- nope
- nu prea
- clar nu

## intent:store_request
- Vreau să reții ceva
- Poți să reții ceva, te rog?
- Memorează
- Memorează ceva
- Reține ceva
- Ține minte
- Memo

## intent:store_location
- [cartea](obj) e [pe masă](location)
- [Cardul de debit](obj) este [în portofelul vechi](location)
- [buletinul meu](obj) se află [în rucsac](location)
- Am pus [foile cu tema la mate](obj) [pe dulapul din sufragerie](location)
- Alex stă [în căminul P5](location)
- Maria Popescu locuiește [pe Bulevardul Timișoara numărul 5](location)
- Bonurile de transport sunt [în plicul de pe raft](location)

## intent:store_attr
- [Mailul](attribute) lui [Alex](person) Marin este alex@marin.com
- [Adresa](attribute) [Elenei](owner) este strada Zorilor numărul 9
- [Numărul de telefon](attribute) al lui [Dan](person) e 123456789
- [numărul blocului](attribute) [fratelui Mihaelei](owner) e 10
- [anul nașterii](attribute) lui [Ștefan](person) cel Mare a fost 1433
- [numele](attribute) [meu](owner) este Gabriel
- cheile [mele](owner) de la casă sunt ușoare

## intent:get_attr
- [Care](query_word) e [mailul](attribute) lui [Mihai](person)?
- [care](query_word) este [numele de utilizator de github](attribute) [al laborantului de EIM](owner)
- poți să-mi spui [care](query_word) era [prețul](attribute) [abonamentului la sală](owner)
- zi-mi [care](query_word) a fost [câștigătorul](attribute) [concursului Eestec Olympics de anul trecut](owner)
- [care](query_word) e adresa colegului meu?
- [care](query_word) era [denumirea bazei de date de la proiect](attribute)?
- [care](query_word) sunt tipurile de rețele neurale
- [Care](query_word) este valoarea de adevăr a propoziției următoare

## intent:get_location
- [Unde](query_word) se află [ochelarii](obj)
- [Unde](query_word) e [buletinul](obj)?
- știi [unde](query_word) am pus [cheile](obj)
- poți să-mi zici [unde](query_word) este [încârcătorul de telefon](obj)
- [unde](query_word) am lăsat [ceasul](obj)?
- [pe unde](query_word) e [sticla de ulei](obj)
- [de unde](query_word) am cumpărat [uscătorul de păr](obj)
- [până unde](query_word) a alergat aseară Marius?

## intent:get_timestamp
- zi-mi [când](query_word) [am fost la sală](action)?
- [De când](query_word) [începe vacanța](action)
- [Până când](query_word) [trebuie trimisă tema](action)
- [cât timp](query_word) [a durat prezentarea temei](action)
- [peste cât timp](query_word) se termină starea de urgență?
- peste [câte](query_word) zile [începe sesiunea de examene](action)
- [Când](query_word) am avut ultimul examen anul trecut?
- [când](query_word) vor avea loc alegerile locale din 2020

## intent:get_subject
- [Cine](query_word) [stă în căminul P16](action)?
- Spune-mi te rog [cine](query_word) [a inventat becul](action)
- [cine](query_word) [a câștigat locul 1 la olimpiada națională de matematică din 2016](action)
- [cine](query_word) [m-a tuns ultima dată](action)?

## intent:get_specifier
- [care](query_word) student a terminat primul tema
- [la ce](query_word) apartament locuiește verișorul meu
- [ce fel de](query_word) imprimantă am acasă
- [în care](query_word) dulap am pus dosarul
- [ce](query_word) examene vor fi date în iunie?
- [despre ce](query_word) operație s-a vorbit
- [de la care](query_word) prieten e cadoul acesta
- [pentru ce](query_word) examen am învățat acum 2 zile
- [pe care](query_word) masă am lăsat ieri periuța de dinți? 


# lookup:query_word
  data/lookup-tables/query-words.txt

## lookup:person
  data/lookup-tables/person.txt
  
## lookup:location
  data/lookup-tables/location.txt