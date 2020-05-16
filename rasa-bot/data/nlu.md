## intent:greet
- hey
- hei
- Salut
- bună
- salutare
- hello
- bună ziua
- hei!
- hi

## intent:goodbye
- bye
- pa
- paa
- pa pa
- mersi
- gata
- super

## intent:affirm
- da
- daa
- da da
- dap
- sigur
- ok
- yep
- yes

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
- reține

## intent:store_location
- cartea e [pe](prep) masă
- Cardul de debit este [în](prep) portofelul vechi
- buletinul meu se află [în](prep) rucsac
- biblioteca se află [la](prep) etajul 5
- service-ul gsm este [pe](prep) strada Ecaterina Teodoroiu numărul 12
- Am pus foile cu tema la mate [pe](prep) dulapul din sufragerie
- Alex stă [în](prep) căminul P5
- Maria Popescu locuiește [pe](prep) Bulevardul Timișoara numărul 5
- Bonurile de transport sunt în plicul de pe raft
- cardul de memorie e [sub](prep) cutia telefonului
- tastatura mea este [în](prep) depozit
- profesorul se află [în](prep) camera vecină
- am lăsat lădița cu cartofi [în](prep) pivniță
- mi-am pus casca de înot [în](prep) dulapul cu tricouri
- geaca de iarnă este [în](prep) șifonierul de acasă

## intent:get_location
- [Unde](query_word_loc) se află ochelarii
- [Unde](query_word_loc) e buletinul?
- știi [unde](query_word_loc) am pus cheile
- poți să-mi zici [unde](query_word_loc) este încârcătorul de telefon
- zi-mi unde am pus ochelarii de înot
- [unde](query_word_loc) am lăsat ceasul?
- [pe unde](query_word_loc) e sticla de ulei
- pe unde mi-am pus pantofii negri
- [de unde](query_word_loc) am cumpărat uscătorul de păr
- de unde au venit cartofii în Europa
- de unde pleacă trenul IR1892
- [până unde](query_word_loc) a alergat aseară Marius?
- până unde au ajuns radiațiile de la Cernobâl

## intent:store_attr
- Mailul lui [Alex](person) Marin [este](a_fi) alex@marin.com
- Adresa [Elenei](owner) [este](a_fi) strada Zorilor numărul 9
- Numărul de telefon al lui [Dan](person) [e](a_fi) 123456789
- numărul blocului [fratelui Mihaelei](owner) [e](a_fi) 10
- anul nașterii lui [Ștefan](person) cel Mare [a fost](a_fi) 1433
- numele [meu](owner) [este](a_fi) Gabriel
- cheile [mele](owner) de la casă sunt ușoare
- adresa de la serviciu este Bulevardul Unirii nr. 0
- numele asistentului de programare paralelă [e](a_fi) Paul Walker
- suprafața apartamentului de la București [este](a_fi) de 58mp
- prețul canapelei a fost de 1300 de lei
- codul de activare al sistemului de operare [e](a_fi) APCHF6798HJ67GI90
- sala laboratorului de PP este EG321
- username-ul meu de github este gabrielboroghina
- seria mea de la buletin este GG2020

## intent:get_attr
- [Care](query_word_which) [e](a_fi) mailul lui [Mihai](person)?
- [care](query_word_which) [este](a_fi) numele de utilizator de github [al laborantului de EIM](owner)
- poți să-mi spui [care](query_word_which) era prețul [abonamentului la sală](owner)
- zi-mi [care](query_word_which) a fost câștigătorul concursului Eestec Olympics de anul trecut
- [care](query_word_which) [era](a_fi) denumirea bazei de date de la proiect?
- [care](query_word_which) [sunt](a_fi) tipurile de rețele neurale
- [care](query_word_which) [este](a_fi) valoarea de adevăr a propoziției
- [care](query_word_which) [e](a_fi) adresa colegului meu?
- [care](query_word_which) [e](a_fi) frecvența procesorului meu
- [care](query_word_which) e numărul lui Radu
- [care](query_word_which) [e](a_fi) limita de viteză în localitate
- [care](query_word_which) e punctul de topire al aluminiului
- [care](query_word_which) [e](a_fi) data de naștere a lui Mihai Popa
- [care](query_word_which) [este](a_fi) mărimea mea la adidași
- [care](query_word_which) este temperatura medie în Monaco în iunie
- [care](query_word_which) [este](a_fi) diferența de vârstă între mine și Vlad
- zi-mi și mie [care](query_word_which) era adresa de căsuță poștală a Karinei Preda
- [care](query_word_which) [sunt](a_fi) datele cardului meu revolut
- [care](query_word_which) este telefonul de la frizerie

## intent:get_specifier
- [ce floare](query_word_spec) s-a uscat
- [ce hackathon](query_word_spec) va avea loc săptămâna viitoare
- [ce windows](query_word_spec) am acum pe calculator
- [ce](query_word_spec) examene vor fi date în iunie?
- [ce temperatură](query_word_spec) a fost în iulie anul trecut
- [ce culoare](query_word_spec) au ochii Andreei
- [ce mail](query_word_spec) am folosit la serviciu
- la [ce apartament](query_word_spec) locuiește verișorul meu
- la [ce sală](query_word_spec) se află microscopul electronic
- la [ce număr](query_word_spec) de telefon se dau informații despre situația actuală
- la [care salon](query_word_spec) este internat bunicul lui
- la [care cod](query_word_spec) poștal a fost trimis pachetul
- la [care hotel](query_word_spec) s-au cazat Mihai și Alex ieri
- [ce fel de imprimantă](query_word_spec)  am acasă
- [ce fel de baterie](query_word_spec) folosește ceasul de mână
- [ce fel de procesor](query_word_spec) are telefonul meu
- [în care](query_word_spec) dulap am pus dosarul
- în [care cameră](query_word_spec) am lăsat încărcătorul de telefon
- în [care săptămână](query_word_spec) e examenul de învățare automată
- de la [care prieten](query_word_spec) e cadoul acesta
- de la [care magazin](query_word_spec) mi-am luat cablul de date?
- pentru [ce test](query_word_spec) am învățat acum 2 zile
- pe [care masă](query_word_spec) am pus ieri periuța de dinți?
- pe [care poziție](query_word_spec) este mașina în parcare
- de pe [care cont](query_word_spec) am plătit factura de curent acum 3 zile
- pe [ce viteză](query_word_spec) am setat aerul condiționat
- pe [ce loc](query_word_spec) am ieșit la olimpiada de info din clasa a 12-a

## intent:get_timestamp
- [când](query_word_time) vor avea loc alegerile locale din 2020
- [Când](query_word_time) am avut ultimul examen anul trecut?
- zi-mi [când](query_word_time) [am fost la sală](action)?
- [De când](query_word_time) [începe vacanța](action)
- [Până când](query_word_time) [trebuie trimisă tema](action)
- [până când](query_word_time) a durat al 2-lea război mondial?
- [până când](query_word_time) trebuie rezolvată problema la vlsi
- [cât timp](query_word_time) [a durat prezentarea temei](action)
- peste [cât timp](query_word_time) se termină starea de urgență?
- peste [cât timp](query_word_time) [începe sesiunea de examene](action)
- când trebuie să merg la control oftalmologic
- [când](query_word_time) trebuie să iau pastilele de stomac

## intent:get_subject
- [Cine](query_word_subj) [stă în căminul P16](action)?
- Spune-mi te rog [cine](query_word_subj) [a inventat becul](action)
- [cine](query_word_subj) [a câștigat locul 1 la olimpiada națională de matematică din 2016](action)
- [cine](query_word_subj) [m-a tuns ultima dată](action)?
- de la [cine](query_word_subj) a cumpărat mihaela cireșele
- de la cine a apărut problema
- [cine](query_word_subj) a fost primul om pe lună?

  
## lookup:query_word_loc
  data/lookup-tables/query-word-loc.txt
  
## lookup:query_word_time
  data/lookup-tables/query-word-time.txt

## lookup:person
  data/lookup-tables/person.txt