package simple.tasks.services;

import services.UpdateTask;

import dto.TasksDto;
import exceptions.ResourceNotFoundException;
import jpa.TasksRepository;
import models.Tasks;
import org.junit.jupiter.api.Test;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class UpdateTaskTest {

    private final TasksRepository tasksRepository = mock(TasksRepository.class);
    private final UpdateTask service = new UpdateTask(tasksRepository);

    @Test
    void shouldUpdateExistingTask() {
        Tasks existing = new Tasks("Old Name");
        TasksDto dto = new TasksDto("New Name");

        when(tasksRepository.findById(1L)).thenReturn(Optional.of(existing));
        when(tasksRepository.save(existing)).thenReturn(existing);

        Tasks result = service.updateTask(1L, dto);
        assertEquals("New Name", result.getName());
        verify(tasksRepository).save(existing);
    }

    @Test
    void shouldThrowIfTaskNotFound() {
        TasksDto dto = new TasksDto("Anything");
        when(tasksRepository.findById(5L)).thenReturn(Optional.empty());

        assertThrows(ResourceNotFoundException.class, () -> service.updateTask(5L, dto));
    }
}

