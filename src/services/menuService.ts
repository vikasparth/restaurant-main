import type { MenuResponse } from "@/types/menu";

export async function fetchMenu(): Promise<MenuResponse> {
// eslint-disable-next-line no-debugger
debugger;
    const response = await fetch("/api/menu");
    if(!response.ok)
    {
        throw new Error("Failed to fetch menu");
      
    }
    return response.json() as Promise<MenuResponse>;

}