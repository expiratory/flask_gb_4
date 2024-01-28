import concurrent
import os
import time
import argparse
import requests
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import aiohttp
import asyncio
from aiohttp import ClientSession


def ensure_folder_exists(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)


def download_image(url, folder='downloads'):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            filename = os.path.join(folder, f"{os.path.basename(url)}")
            ensure_folder_exists(folder)
            with open(filename, 'wb') as file:
                file.write(response.content)
            return filename
        else:
            return None
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None


async def async_download_image(url, folder='downloads'):
    try:
        async with ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    filename = os.path.join(folder, f"{os.path.basename(url)}")
                    ensure_folder_exists(folder)
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as resp:
                            with open(filename, 'wb') as file:
                                file.write(await resp.read())
                    return filename
                else:
                    return None
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None


def download_images(urls, concurrency_type='thread', folder='downloads'):
    start_time = time.time()

    with get_executor(concurrency_type) as executor:
        futures = {executor.submit(download_image, url, folder): url for url in urls}

        for future in concurrent.futures.as_completed(futures):
            url = futures[future]
            try:
                filename = future.result()
                if filename:
                    print(f"Downloaded {url} to {filename} in {time.time() - start_time:.2f} seconds")
            except Exception as e:
                print(f"Error downloading {url}: {e}")

    print(f"Total execution time: {time.time() - start_time:.2f} seconds")


async def async_download_images(urls, folder='downloads'):
    start_time = time.time()

    async def download_all_images():
        tasks = []
        async with ClientSession() as session:
            for url in urls:
                tasks.append(async_download_image(url, folder))
            return await asyncio.gather(*tasks)

    downloaded_files = await download_all_images()

    for filename in downloaded_files:
        if filename:
            print(f"Downloaded {filename} in {time.time() - start_time:.2f} seconds")

    print(f"Total execution time: {time.time() - start_time:.2f} seconds")


def get_executor(concurrency_type):
    if concurrency_type == 'thread':
        return ThreadPoolExecutor(max_workers=5)
    elif concurrency_type == 'process':
        return ProcessPoolExecutor(max_workers=5)
    else:
        raise ValueError("Invalid concurrency type")


async def run_async_download_images(urls):
    await async_download_images(urls)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download images from URLs.')
    parser.add_argument('urls', nargs='+', help='List of image URLs')
    parser.add_argument('--concurrency', choices=['thread', 'process', 'async'], default='thread',
                        help='Concurrency type: thread, process, or async')
    args = parser.parse_args()

    if args.concurrency == 'async':
        asyncio.run(run_async_download_images(args.urls))
    else:
        download_images(args.urls, args.concurrency)
