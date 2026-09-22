using UnityEngine;

namespace Lab01.AI
{
    // WASD перемещает капсулу игрока; камера следует за ней.
    [RequireComponent(typeof(CharacterController))]
    public class PlayerController : MonoBehaviour
    {
        [SerializeField] private float speed = 4f;
        private CharacterController controller;
        private void Awake() => controller = GetComponent<CharacterController>();
        private void Update()
        {
            Vector3 direction = new Vector3(Input.GetAxisRaw("Horizontal"), 0, Input.GetAxisRaw("Vertical"));
            controller.SimpleMove(direction.normalized * speed);
        }
    }
}
