package simple.tasks.services;

import services.TasksGetAllTasks;
import main.java.simple.tasks.jpa.*;
import simple.tasks.models.Tasks;
import org.junit.jupiter.api.Test;

import java.util.Arrays;
import java.util.List;

import static org.mockito.Mockito.*;
import static org.junit.jupiter.api.Assertions.*;

class TasksGetAllTasksTest {

    private final TasksRepository tasksRepository = mock(TasksRepository.class);
    private final TasksGetAllTasks service = new TasksGetAllTasks(tasksRepository);

    @Test
    void shouldReturnAllTasks() {
        List<Tasks> mockTasks = Arrays.asList(
            new Tasks("Task 1"),
            new Tasks("Task 2")
        );

        when(tasksRepository.findAll()).thenReturn(mockTasks);

        List<Tasks> result = service.getAllTasks();
        assertEquals(2, result.size());
        assertEquals("Task 1", result.get(0).getName());
        assertEquals("Task 2", result.get(1).getName());
    }
}
