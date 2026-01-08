using UnityEngine;

public class AutoMinecraft : MonoBehaviour
{
    [Header("Настройки мира")]
    public int size = 20; // Размер карты
    
    private float rotX, rotY;

    void Start()
    {
        // 1. Настройка камеры и игрока
        gameObject.AddComponent<CharacterController>();
        Cursor.lockState = CursorLockMode.Locked;

        // 2. Генерация мира
        for (int x = 0; x < size; x++)
        {
            for (int z = 0; z < size; z++)
            {
                // Создаем рельеф через шум Перлина
                int height = Mathf.FloorToInt(Mathf.PerlinNoise(x * 0.1f, z * 0.1f) * 4);
                
                for (int y = 0; y <= height; y++)
                {
                    CreateBlock(x, y, z, y == height);
                }
            }
        }
    }

    void CreateBlock(int x, int y, int z, bool isGrass)
    {
        GameObject cube = GameObject.CreatePrimitive(PrimitiveType.Cube);
        cube.transform.position = new Vector3(x, y, z);
        
        // Автоматическая покраска без текстур!
        Renderer rend = cube.GetComponent<Renderer>();
        if (isGrass)
            rend.material.color = new Color(0.2f, 0.8f, 0.2f); // Зеленый (kras)
        else
            rend.material.color = new Color(0.4f, 0.2f, 0.1f); // Коричневый (ear)
    }

    void Update()
    {
        // FPS Управление
        float speed = 5f;
        float sens = 2f;

        // Повороты
        rotX += Input.GetAxis("Mouse X") * sens;
        rotY -= Input.GetAxis("Mouse Y") * sens;
        rotY = Mathf.Clamp(rotY, -90, 90);
        transform.rotation = Quaternion.Euler(rotY, rotX, 0);

        // Движение
        float moveF = Input.GetAxis("Vertical") * speed * Time.deltaTime;
        float moveS = Input.GetAxis("Horizontal") * speed * Time.deltaTime;
        transform.Translate(moveS, 0, moveForward);

        // Ломание блоков (ЛКМ)
        if (Input.GetMouseButtonDown(0))
        {
            Ray ray = new Ray(transform.position, transform.forward);
            if (Physics.Raycast(ray, out RaycastHit hit, 5f))
                Destroy(hit.transform.gameObject);
        }
    }
}
