import os
import shutil

class FileManager:
    """파일 정리 및 관리 클래스"""
    
    def __init__(self):
        pass
    
    def scan_folders(self, root_path, depth=2):
        """
        루트 폴더 하위의 모든 폴더를 스캔합니다.
        
        Args:
            root_path: 스캔할 루트 폴더 경로
            depth: 검색할 깊이 (1 = 직계 하위, 2 = 하위의 하위까지)
        
        Returns:
            dict: {폴더명: 전체경로} 형태의 딕셔너리
        """
        folder_map = {}
        
        if not os.path.exists(root_path):
            return folder_map
        
        try:
            for root, dirs, _files in os.walk(root_path):
                relative_path = os.path.relpath(root, root_path)
                current_depth = 0 if relative_path == '.' else relative_path.count(os.sep) + 1
                
                if current_depth >= depth:
                    dirs.clear()
                    continue
                
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    folder_map[dir_name] = dir_path
                    
        except Exception as e:
            print(f"폴더 스캔 오류: {str(e)}")
        
        return folder_map
    
    def find_matching_folders(self, promotion_number, folder_map):
        """
        프로모션 번호가 포함된 모든 폴더를 찾습니다.
        
        Args:
            promotion_number: 찾을 프로모션 번호
            folder_map: scan_folders()에서 반환한 폴더 맵
        
        Returns:
            list: 매칭된 폴더 경로의 리스트
        """
        matching_folders = []
        
        for folder_name, folder_path in folder_map.items():
            if promotion_number in folder_name:
                matching_folders.append(folder_path)
        
        return matching_folders
    
    def organize_file(self, source_path, target_folders):
        """
        파일을 대상 폴더(들)로 이동/복사합니다.
        
        Args:
            source_path: 원본 파일 경로
            target_folders: 대상 폴더 경로 리스트
        
        Returns:
            tuple: (성공여부, 메시지, 복사된폴더수)
        """
        if not target_folders:
            return (False, "매칭되는 폴더가 없습니다", 0)
        
        if not os.path.exists(source_path):
            return (False, "원본 파일이 존재하지 않습니다", 0)
        
        filename = os.path.basename(source_path)
        
        try:
            if len(target_folders) == 1:
                target_path = self._get_unique_path(target_folders[0], filename)
                shutil.move(source_path, target_path)
                return (True, f"이동 완료: {os.path.basename(target_folders[0])}", 1)
            
            else:
                success_count = 0
                folder_names = []
                
                for folder in target_folders:
                    try:
                        target_path = self._get_unique_path(folder, filename)
                        shutil.copy2(source_path, target_path)
                        success_count += 1
                        folder_names.append(os.path.basename(folder))
                    except Exception as e:
                        print(f"복사 실패 ({folder}): {str(e)}")
                
                if success_count == len(target_folders):
                    os.remove(source_path)
                    return (True, f"중복 폴더 복사 완료: {', '.join(folder_names)}", success_count)
                elif success_count > 0:
                    return (False, f"일부 폴더에만 복사됨 ({success_count}/{len(target_folders)}). 원본 파일 유지.", success_count)
                else:
                    return (False, "모든 폴더에 복사 실패", 0)
                
        except Exception as e:
            return (False, f"파일 처리 오류: {str(e)}", 0)
    
    def _get_unique_path(self, folder, filename):
        """파일명이 중복되지 않도록 유니크한 경로를 생성합니다."""
        base_path = os.path.join(folder, filename)
        
        if not os.path.exists(base_path):
            return base_path
        
        name, ext = os.path.splitext(filename)
        counter = 1
        while True:
            new_path = os.path.join(folder, f"{name}_{counter}{ext}")
            if not os.path.exists(new_path):
                return new_path
            counter += 1
