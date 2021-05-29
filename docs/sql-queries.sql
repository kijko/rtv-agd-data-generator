-- wyswietla produkty kupione przez osobę POOR-1 dnia symulacji 2021-01-10
select P.name, P.price
from ordered_product OP
         join product P on P.id = OP.product_id
         join customer_order CO on CO.id = OP.order_id
         join visit V on V.id = CO.visit_id
where V.customer_id = 'POOR-1'
  and V.visit_at = '2021-01-10';

-- zawraca daty w ktorych osoba POOR-1 poszła do sklepu
select visit_at from visit where customer_id = 'POOR-1';

-- zwraca wszystkie osoby z danej grupy (POOR)
select * from customer where group_name = 'POOR';
