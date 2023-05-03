# Get information about installed packages
installed_packages <- installed.packages()

# Get library paths and package names
library_paths <- installed_packages[, "LibPath"]
package_names <- rownames(installed_packages)

# Print the package filepaths
print(package_names)