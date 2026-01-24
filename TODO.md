### Actualizacion del precio
Si la request del cliente no le llega al nodo lider, o que ese nodo redirija la request al lider (de esa forma el cliente va a poder ejecutar cualquier comando / solicitud a cualquier nodo, total el nodo se encarga de redirijir al lider lo que es necesario) o que el cliente sepa en todo momento cual es el lider para solamente hacerle a el la request de actualizar el precio. Si no es el lider el que recibe el comando, tiene de bueno esto que el sistema es bien transparente para el usuario.

La actualizacion del precio la podemos hacer como una transaccion clasica o parcial. La clasica en donde si se actualiza el precio de un producto, o se actualizan todos los nodos o ninguno. La parcial en donde se actualizan los precios de los nodos que estan vivos, y los caidos una vez que se despierten tendran que avisarle al lider de esto para que les diga como actualizar y que. El lider deberia saber cuales son los nodos que no pudo actualizar y que no pudo actualizar en el. Hay que asumir tambien que los mensajes pueden llegar tarde o que pueden no llegar en el mismo orden a todos los nodos, por lo que hay que tener cuidado con eso. Hay que hacer un broadcast y que ese broadcast al menos nos aseguremos de que es secuencial (cada transaccion tenga un numero de secuencia). El broadcast es facil de hacer, solo garantizar la secuencialidad, con numeros de sencuencia.

A esto lo implemente con un 2PC, pero tengo una duda. Que pasa si el lider le manda a los nodes el prepare commit y todos responden que si, y cuando despues el lider les da el okay todos actualizan su precio. Pero que pasa si entre medio un nodo falla, despues de haber dado el okay? Despues cuando vuelve a estar running tendra un precio incorrecto.

## PROBLEMAS:
### ver que onda la secuencialidad del broadcast que estoy haciendo:
que hice: como tecnicamente los mensajes pueden llegar fuera de orden, por ejemplo C1 -> C2 es recibido por un nodo como C2 -> C1 deberia aplicar C2 pero no C1 despues. Entonces las transacciones tienen versiones, los productos tambien, cada transaccion viene con una version asociada y en base a esa aplica el cambio o no.

### ver lo del numero de secuencia de cada transaccion (no comprarten el mismo nro entre nodos)
Hay un problema aca, como los nodos no comparten el transaction id counter, puede darse el caso en donde el lider ejecuta la transaccion con id 1 y despues cambia el lider que tambien ejecuta la transaccion 1. pero si el nodo entre medio le llego tarde el mensaje del commit de al primera tranasaccion, y llego antes el prepare de la transaccion del segundo lider, ahi tenemos un problema. (NO LO RESOLVI)

- si un nodo falla despues de haber respondido con True al prepare y antes de hacer el commit que pasaria?


nodoFollower -> [T1] (mesaje recibido prepare)

n1Lider prepare (T1) commit 

n2Lider prepare (T1) 




# Price Update
Implemente un 2FC, en donde la actualizacion de un precio se hace en dos etapas. La actualizacion de un precio se hace en todos los peers o en ninguno. Si hay un peer caido o que por alguna razon no conteste, no se hace la actualizacion en ninguno. Primero si la request de actualizar un precio le llega a un nodo que no es el lider, este nodo se encarga de reenviarle la request al lider para que la resuelva. Cuando el lider recibe esta request, lo que hace primero es generar un nuevo id de transaccion y empieza la primera etapa. El lider prepara localmente el cambio y le comunica a todos los peers que preparen el cambio. Esta preparacion del cambio es insertar esta transaccion con sus datos en el diccionario de transacciones que cada nodo tiene. Estas son transacciones pendientes, no se han aplicado todavia. 
Cada nodo entonces que recibe la orden, prepara esta actualizacion. Si hay algun nodo que no pudo lograr esto, el lider inmediatamente aborta la transaccion completa, borra esa entrada correspondiente a la transaccion del diccionario suyo y del resto de los peers.
En caso en que todos los peers hayan podido lograr esta preparacion, empieza la segunda etapa que es el commit. El lider hace el commit local, en donde se actualiza el precio en base a los datos de esa transaccion y se elimina la entrada correspondiente del diccionario. Lo mismo es ordenado para todos los nodos, quienes realizaran esto localmente.

### Puntos a tener en cuenta:
#### Secuencialidad del broadcast
No debemos asumir ni que el broadcast es secuencial ni que los mensajes llegan siempre a tiempo. Puede pasar que los mensajes lleguen tarde e inclusive desordenados. Para solucionar este problema, hice lo siguiente:
Tomemos el siguiente ejemplo: se realizan dos actualizaciones de precio de un mismo producto: C1 -> C2. Esta actualizacion es recibida por un nodo como C2 -> C1, en donde deberia aplicar C2 e ignorar C1 porque este ultimo termina siendo un precio viejo.
Para evitar que se provoquen inconsistencias de este tipo, los productos tienen versiones. Cada transaccion viene con una version asociada y en base a esa el nodo aplica el cambio o no. Un nodo puede haber recibido los mensajes desordenados como C2 -> C1, pero al aplicarlos, comparara la version de las transacciones con la version del producto para decidir si aplicar el cambio o no.
Por ejemplo, tenemos el producto 'Manzana' con la ultima version de cambio '3'. Cuando intenta aplicar la actualizacion correspondiente a C2 (cuya version es '5'), lo realiza ya que 3 < 5. Pero cuando despues le llega el mensaje de aplicar el cambio C1 (con version 4), no lo va a ejecutar porque 5 > 4. Y con esto se evita el problema de la secuencialidad de los mensajes. 
En el caso en que los mensajes lleguen tarde, tampoco habria problema creo porque si llegan tarde en algun momento se van a aplicar y no se van a aplicar si no es correcto que eso pase gracias a las versiones que tienen los productos.

#### Id de las transacciones
La implementacion que yo hice asigna un id a cada nueva transaccion que se haga (cada transaccion es una nueva actualizacion de un precio de un producto que sera aplicada o no a todos los nodos. Y sera insertada en el diccionario de cada uno para su commit o abort dependiendo de la situacion). El problema es que cada nodo tiene un atributo transaction_counter que es aumentado cada vez que se hace una nueva transaccion. Hay un problema aca, como los nodos NO comparten el transaction id counter, puede darse el caso en donde el lider ejecuta la transaccion con id 1 y despues cambia el lider que tambien ejecuta la transaccion 1. pero si el nodo entre medio le llego tarde el mensaje del commit de la primera tranasaccion, y llego antes el prepare de la transaccion del segundo lider, ahi tenemos un problema porque el nodo tendria que agregar a su diccionario otra transaccion con el mismo ID que la primera que todavia tiene guardada ahi. (NO LO RESOLVI a este problema)

# Buying a product 
La venta de un producto se puede hacer desde cualquier nodo. Cuando un nodo recibe la request de venta de un producto, primero intenta vender ese producto localmente. En el deposito de cada nodo hay un metodo llamado sell_product en donde vende la cantidad requerida por el cliente de ese producto. Si el nodo tiene la cantidad total requerida, retorna 0, porque se pudieron vender todas las unidades y no quedo ninguna por ser vendida. Si el nodo no tiene ninguna unidad para vender, retornara la cantidad requerida por el cliente. Y si tiene unidades para vender pero no la cantidad total, vende lo que puede y retorna el numero de unidades que no pudo vender.
En base a esto, el nodo tendra que consultar con sus peers si pueden venderle al cliente las unidades restantes en base a la variable remaining que indica las unidades que todavia faltan por vender. Esto se repite hasta que se vendan todas las unidades o hasta que se haya consultado con todos los nodos. Si el cliente por ejemplo quiere comprar 5 manzanas y entre todos los nodos de la red solamente hay 4, se venderan 4 en total. Siempre se intenta vender la mayor cantidad que se disponga en base a lo que pide el cliente.

# Get product price
Lo que hace es simple, al nodo que le llega esta request, consulta localmente el precio de ese producto y le responde al cliente.


A mi me quedo hacer esto: escribir tests en la carpeta tests sobre mis metodos (price update, buy product, get price).
Otra cosa que queda para hacer: habiamos dicho de hacer una especie de menu para el cliente, para que pueda elegir entre todas las opciones de requests que puede hacer.
Ademas, tenemos que preparar un escenario, un ejemplo en donde hacemos una especie de demo para que se vea como funciona el tp. Tenemos que ver como modelar que un nodo falle para que veamos como el programa se comporta en base a eso. 
GRPC puede usar TCP o UDP, ver que estamos usando nosotros.



#### DUDAS
* Si un nodo falla despues de haber respondido con True al prepare y antes de hacer el commit de una actualizacion de un precio que pasaria?
*  esta bien tener un lock en la eleccion para que solo un nodo pueda llevar a cabo la eleccion del lider?

### TODOs
1) Resolver el problema de election_id
2) Preparar un ejemplo para la demo
3) Escribir el informe