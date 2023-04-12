import torch


def can_access_cuda():
    return ("Torch can access CUDA: " + str(torch.cuda.is_available()))


def random_vector():
    # Set fixed seed
    torch.manual_seed(0)

    # Generate "random" matrix
    outList = torch.randn(3, 9).tolist()

    if (outList == [[-1.1258398294448853, -1.152360200881958, -0.2505785822868347, -0.4338788092136383, 0.8487103581428528, 0.6920091509819031, -0.31601276993751526, -2.1152193546295166, 0.32227492332458496], [-1.2633347511291504, 0.34998318552970886, 0.26604941487312317, 0.16645534336566925, 0.8743818402290344, -0.14347384870052338, -0.1116093322634697, -0.6135830879211426, 0.03159274160861969], [-0.4926769733428955, 0.05373690277338028, 0.6180566549301147, -0.41280221939086914, -0.8410648107528687, -2.316041946411133, -0.10230965167284012, 0.7924439907073975, -0.28966769576072693]]):
        return ("Test passed!")
    else:
        raise Exception("Test failed...output was " + str(outList))


def matrix_multiplication():
    # Test 2 - Element-wise multiplication w/CUDA

    if torch.cuda.is_available():
        device = torch.device("cuda")
    else:
        raise Exception("CUDA is not accessible/GPU not found. Test failed...")

    # Define tensors and move to device
    a = torch.tensor([1, 2, 3], dtype=torch.float32).to(device)
    b = torch.tensor([4, 5, 6], dtype=torch.float32).to(device)

    # Perform element-wise multiplication and check result
    c = a * b
    outList = c.tolist()
    if (outList == [4.0, 10.0, 18.0]):
        return ("Test passed!")
    else:
        raise Exception("Test failed...output was " + str(outList))

    # NOTE: If you encounter CUDA error: out of memory, please restart your docker container.
    # The current assigned GPU is out of free NVRAM.


def neural_network():
    # Test 3 - Define basic neural network w/CUDA

    import torch.nn as nn

    # Define the network architecture
    class Net(nn.Module):
        def __init__(self):
            super(Net, self).__init__()
            # Input layer has 2 nodes, hidden layer has 4 nodes
            self.fc1 = nn.Linear(2, 4)
            # Set weight and bias to fixed values
            self.fc1.weight.data.fill_(1.0)
            self.fc1.bias.data.fill_(0.0)
            self.fc2 = nn.Linear(4, 1)  # Output layer has 1 node
            # Set weight and bias to fixed values
            self.fc2.weight.data.fill_(1.0)
            self.fc2.bias.data.fill_(0.0)

        def forward(self, x):
            x = nn.functional.relu(self.fc1(x))
            x = self.fc2(x)
            return x

    # Instantiate the network
    net = Net()

    # Define the input to the network
    input = torch.tensor([[1.0, 2.0]])

    # Move the PyTorch tensors and neural network to the GPU device
    if torch.cuda.is_available():
        device = torch.device("cuda")
    else:
        raise Exception("CUDA is not accessible/GPU not found. Test failed...")
    net.to(device)
    input = input.to(device)

    # Use the PyTorch functions that are specifically designed for GPU computations
    net.cuda()
    input.cuda()

    # Pass the input through the network and get the output
    outList = net(input).tolist()

    # Check output
    if (outList == [[12.0]]):
        return ("Test passed!")
    else:
        raise Exception("Test failed...output was " + str(outList))


def length_of_dataset_no_cuda():
    # Test 4 - Calculate dataset length w/out CUDA

    from torchvision import datasets, transforms

    # Define a transform to convert the data to a tensor
    transform = transforms.ToTensor()

    # Download and load the training data
    train_data = datasets.MNIST(
        root='./data', train=True, download=True, transform=transform)

    # Check the size of the training set
    ld = len(train_data)
    if (ld == 60000):
        return ("Test passed!")
    else:
        raise Exception("Test failed...output was " + str(ld))


def mean_pixel_value_cuda():
    # Test 5 - Calculate mean pixel values from MNIST dataset w/CUDA

    from torchvision import datasets, transforms

    # Define device
    if torch.cuda.is_available():
        device = torch.device("cuda")
    else:
        raise Exception("CUDA is not accessible/GPU not found. Test failed...")

    # Load MNIST dataset
    transform = transforms.Compose(
        [transforms.ToTensor(), transforms.Normalize((0.5,), (0.5,))])
    train_set = datasets.MNIST(
        root='./data', train=True, download=True, transform=transform)
    test_set = datasets.MNIST(
        root='./data', train=False, download=True, transform=transform)

    # Move dataset to device
    train_loader = torch.utils.data.DataLoader(
        train_set, batch_size=64, shuffle=True, pin_memory=True, num_workers=2)
    test_loader = torch.utils.data.DataLoader(
        test_set, batch_size=64, shuffle=True, pin_memory=True, num_workers=2)

    # Calculate mean value of dataset
    mean = torch.mean(train_set.data.float() / 255)

    # Use mean value as fixed value
    output = mean.item()

    # Check truncated value
    trunc = round(output, 10)
    if (trunc == 0.1306604743):
        return ("Test passed!")
    else:
        raise Exception("Test failed...(truncated) output was " + str(trunc))


def multiply_dataset_calculate_mean_cuda():
    # Test 6 - Multiplies MNIST dataset by 2, calculates mean of first 100 elements w/CUDA

    from torchvision import datasets, transforms

    # Set the fixed seed for CPU and GPU (if available)
    torch.manual_seed(0)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(0)
    else:
        raise Exception("CUDA is not accessible/GPU not found. Test failed...")

    # Download the MNIST dataset nb
    transform = transforms.Compose(
        [transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))])
    train_dataset = datasets.MNIST(
        './data', train=True, download=True, transform=transform)

    # Create a DataLoader for the dataset
    train_loader = torch.utils.data.DataLoader(
        train_dataset, batch_size=64, shuffle=True)

    # Move the data to GPU
    device = torch.device('cuda')
    train_loader = [(data.to(device), target.to(device))
                    for data, target in train_loader]

    # Apply a simple operation using GPU
    for batch_idx, (data, target) in enumerate(train_loader):
        output = data * 2
        if batch_idx == 0:
            exactFloat = torch.mean(target[:100].float()).item()
            if (exactFloat == 4.734375):
                return ("Test passed!")
            else:
                raise Exception("Test failed...output was " + str(exactFloat))


def test_can_access_cuda():
    result = can_access_cuda()
    assert result == "Torch can access CUDA: True"


def test_random_vector():
    result = random_vector()
    assert result == "Test passed!"


def test_matrix_multiplication():
    result = matrix_multiplication()
    assert result == "Test passed!"


def test_neural_network():
    result = neural_network()
    assert result == "Test passed!"


def test_length_of_dataset_no_cuda():
    result = length_of_dataset_no_cuda()
    assert result == "Test passed!"


def test_mean_pixel_value_cuda():
    result = mean_pixel_value_cuda()
    assert result == "Test passed!"


def test_multiply_dataset_calculate_mean_cuda():
    result = multiply_dataset_calculate_mean_cuda()
    assert result == "Test passed!"
